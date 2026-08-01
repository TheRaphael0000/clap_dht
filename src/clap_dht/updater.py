
import asyncio
import glob
import argparse
import os

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import exists, select
import dotenv

from .db import Embedding
from .processing import EmbeddingModel, compute_fingerprint
from .db import DB
from .utils import logger


class Updater:
    def __init__(self, drop_all):
        self.db = DB()
        self.db.init(drop_all=drop_all)

        self.embedding_model = EmbeddingModel()


    async def process(self, filepath, force=False):
        logger.info(f"Processing: '{filepath}'")

        fingerprint = await compute_fingerprint(filepath)
        embedding = self.embedding_model.compute_embedding(filepath)

        with self.db as session:
            stmt = insert(Embedding).values(path=filepath, embedding=embedding, fingerprint=fingerprint)

            if force:
                stmt = stmt.on_conflict_do_update(
                    index_elements=["path"],
                    set_=dict(embedding=embedding, fingerprint=fingerprint),
                )

            session.execute(stmt)
            session.commit()
            logger.info(f"Inserted: '{filepath}'")
                


    async def update_db(self, force=False):
        folder = os.getenv('ROOT_DIR')
        logger.info(f"Stating database update with: {folder}")

        for filepath in glob.iglob(f"{folder}/**", recursive=True):
            if not os.path.isfile(filepath):
                continue

            stmt = select(exists().where(Embedding.path == filepath))

            with self.db as session:
                is_exist = session.scalar(stmt)

            if is_exist and not force:
                logger.info(f"Already in db: {filepath}")
                continue

            await self.process(filepath, force)


def main():
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(prog='myprogram')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--drop', action='store_true')

    args = parser.parse_args()
    updater = Updater(drop_all=args.drop)
    
    asyncio.run(updater.update_db(args.force))
