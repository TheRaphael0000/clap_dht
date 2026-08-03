import os
import pathlib
import logging
import threading
import queue

from sqlalchemy.dialects.postgresql import insert

from torch.utils.data import DataLoader

from clap_dht.processing import AudioFeatureExtractor
from clap_dht.db import DB, Embedding
from clap_dht.updater.filesystem_dataset import FilesystemDataset

logger = logging.getLogger()

class Updater:
    def __init__(self, drop_all, batch_size=8, force_process=False):
        self.root_dir = pathlib.Path(os.getenv('ROOT_DIR'))
        self.db = DB()
        self.db.init(drop_all=drop_all)

        self.dataset = FilesystemDataset(self.root_dir, force_process)
        self.dataloader = DataLoader(self.dataset, batch_size=batch_size, prefetch_factor=1, num_workers=1)
        
        self.audio_feature_extractor = AudioFeatureExtractor()
        self.to_save_queue = queue.Queue()
        

    def saver(self):
        logger.info(f"Starting saver process")
        while True:
            data = self.to_save_queue.get()

            if data is None:
                logger.info(f"Stopping saver process")
                return
            
            subpaths, results = data
            
            logger.info(f"Saving batch start ({len(results)}/{len(subpaths)})...")

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

            logger.info(f"Saving batch end")


    def start(self):
        logger.info(f"Stating database update with: {self.root_dir}")

        saver = threading.Thread(target=self.saver)
        saver.start()

        for audio_bytes, subpaths in self.dataloader:
            logger.info(f"Processing batch ({len(subpaths)})...")
            results = self.audio_feature_extractor.process_batch(audio_bytes, subpaths)
            logger.info(f"Processing batch end ({len(results)})")

            self.to_save_queue.put((subpaths, results))

        self.to_save_queue.put(None)
        saver.join()
        logger.info(f"Update completed")
