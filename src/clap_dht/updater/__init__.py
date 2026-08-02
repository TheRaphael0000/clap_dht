import os
import pathlib

from sqlalchemy.dialects.postgresql import insert

from torch.utils.data import DataLoader
import torch.multiprocessing as mp

from clap_dht.processing import AudioFeatureExtractor
from clap_dht.db import DB, Embedding
from clap_dht.utils import logger

from clap_dht.updater.dataset import AudioBytesDataset



class Updater:
    def __init__(self, drop_all, batch_size=8, force_process=False):
        self.root_dir = pathlib.Path(os.getenv('ROOT_DIR'))
        self.db = DB()
        self.db.init(drop_all=drop_all)

        self.dataset = AudioBytesDataset(self.root_dir, force_process)
        self.dataloader = DataLoader(self.dataset, batch_size=batch_size, prefetch_factor=3, num_workers=1)
        
        self.audio_feature_extractor = AudioFeatureExtractor()
        self.to_save_queue = mp.Queue()
        

    def saver(self):
        while True:
            subpaths, results = self.to_save_queue.get()

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

        saver = mp.Process(target=self.saver)
        saver.start()

        for audio_bytes, subpaths in self.dataloader:
            logger.info(f"Processing batch ({len(subpaths)})...")
            results = self.audio_feature_extractor.process_batch(audio_bytes, subpaths)

            logger.info(f"Saving batch ({len(subpaths)})...")
            self.to_save_queue.put(subpaths, results)
