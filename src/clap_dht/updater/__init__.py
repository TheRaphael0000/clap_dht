import os
import pathlib
import io

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import exists, select
import filetype

from clap_dht.processing import AudioFeatureExtractor
from clap_dht.db import DB, Embedding
from clap_dht.utils import logger


class Updater:
    def __init__(self, drop_all, batch_size=8):
        self.root_dir = pathlib.Path(os.getenv('ROOT_DIR'))
        self.db = DB()
        self.db.init(drop_all=drop_all)
        self.batch_size = batch_size
        self.audio_feature_extractor = AudioFeatureExtractor()


    def update_db(self, force=False):
        logger.info(f"Stating database update with: {self.root_dir}")

        batch = []

        for fullpath in pathlib.Path(self.root_dir).rglob("*"):
            subpath = str(fullpath.relative_to(self.root_dir))
            fullpath = str(fullpath)

            if not os.path.isfile(fullpath):
                continue

            with self.db as session:
                is_exist = session.scalar(select(exists().where(Embedding.path == subpath)))

            if is_exist and not force:
                logger.info(f"Already in db: '{subpath}'")
                continue

            logger.info(f"Loading: '{subpath}'")
            audio_bytes = open(fullpath, "rb").read()

            kind = filetype.guess(audio_bytes)
            if kind is None or not kind.mime.startswith("audio"):
                continue

            batch.append((audio_bytes, subpath))

            if len(batch) >= self.batch_size:
                self.process(batch, force)
                batch = []
            
        # process if we reached the end of the iterator
        self.process(batch, force)


    def process(self, batch, force=False):
        logger.info(f"Processing batch ({len(batch)})...")
        results = self.audio_feature_extractor.process_buffers([a for a, p in batch])

        logger.info(f"Saving batch ({len(batch)})...")

        payload = [
            {
                "path": subpath,
                "fingerprint": fingerprint,
                "embedding": embedding,
            }
            for (_, subpath), (fingerprint, embedding) in zip(batch, results)
        ]
        stmt = insert(Embedding).values(payload)
        
        if force:
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

        # with self.db as session:
        #     for (_, subpath), (fingerprint, embedding) in zip(batch, results):

        #         stmt = insert(Embedding).values(path=subpath, fingerprint=fingerprint, embedding=embedding)

        #         if force:
        #             stmt = stmt.on_conflict_do_update(
        #                 index_elements=["path"],
        #                 set_=dict(fingerprint=fingerprint, embedding=embedding),
        #             )

        #         session.execute(stmt)
        #         session.commit()
