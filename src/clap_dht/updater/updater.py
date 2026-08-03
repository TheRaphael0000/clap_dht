import os
import pathlib
import logging
import threading
import queue
import atexit

from sqlalchemy.dialects.postgresql import insert

from torch.utils.data import DataLoader

from clap_dht.db import DB, Embedding
from clap_dht.updater.audio_feature_extractor import AudioFeatureExtractor
from clap_dht.updater.filesystem_dataset import FilesystemDataset

from clap_dht.utils import Timer

logger = logging.getLogger()


def dataloader_cleanup(dataloader_instance=None):
    logger.info("Cleaning up child processes...")
    if dataloader_instance and hasattr(dataloader_instance, "_iterator"):
        try:
            dataloader_instance._iterator._shutdown_workers()
        except Exception:
            pass

class Updater:
    def __init__(self, drop_all, batch_size, max_workers, force_process, prefetch_factor, ignore_existing_fingerprint):
        self.root_dir = pathlib.Path(os.getenv('ROOT_DIR'))
        self.db = DB()
        self.db.init(drop_all=drop_all)

        self.dataset = FilesystemDataset(self.root_dir, force_process)
        self.dataloader = DataLoader(self.dataset, batch_size=batch_size, prefetch_factor=prefetch_factor, num_workers=1)
        
        atexit.register(dataloader_cleanup, self.dataloader)
        
        self.audio_feature_extractor = AudioFeatureExtractor(max_workers, ignore_existing_fingerprint)
        self.to_save_queue = queue.Queue()
        

    def saver(self):
        with Timer("Saver"):
            while True:
                data = self.to_save_queue.get()
                if data is None:
                    logger.info(f"Stopping saver process")
                    return
                
                i, subpaths, results = data

                with Timer(f"Saving batch {i}", info=True):
                    payload = [
                        {
                            "path": subpath,
                            "fingerprint": fingerprint,
                            "embedding": embedding,
                        }
                        for subpath, (fingerprint, embedding) in zip(subpaths, results)
                    ]
                    stmt = insert(Embedding).values(payload)
                    
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["path"],
                        set_={
                            "fingerprint": stmt.excluded.fingerprint,
                            "embedding": stmt.excluded.embedding,
                        },
                    )

                    with self.db as session:
                        session.execute(stmt)
                        session.commit()



    def start(self):
        logger.info(f"Stating database update with: {self.root_dir}")

        saver = threading.Thread(target=self.saver)
        saver.start()

        for i, (audio_bytes, subpaths) in enumerate(self.dataloader):
            with Timer(f"Processing batch {i}", info=True):
                results = self.audio_feature_extractor.process_batch(audio_bytes, subpaths)
                self.to_save_queue.put((i, subpaths, results))

        self.to_save_queue.put(None)
        saver.join()
        logger.info(f"Update completed")


