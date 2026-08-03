import os
import pathlib

from sqlalchemy import exists, select
import filetype

from torch.utils.data import IterableDataset

from clap_dht.db import DB, Embedding

import logging
logger = logging.getLogger()

class DBChecker:
    def __init__(self):
        self.db = DB()

    def check(self, subpath):
        with self.db as session:
            is_exist = session.scalar(select(exists().where(Embedding.path == subpath)))
            if is_exist:
                return True
        return False



class FilesystemDataset(IterableDataset):
    def __init__(self, root_dir, force_process):
        self.root_dir = root_dir
        self.force_process = force_process
        self.db_checker = DBChecker()

    def __iter__(self):
        for fullpath in pathlib.Path(self.root_dir).rglob("*"):
            subpath = str(fullpath.relative_to(self.root_dir))
            fullpath = str(fullpath)

            if not os.path.isfile(fullpath):
                continue

            if not self.force_process:
                if self.db_checker.check(subpath):
                    logger.info(f"Skipped (already in db): '{subpath}'")
                    continue

            audio_bytes = open(fullpath, "rb").read()

            if not filetype.is_audio(audio_bytes):
                logger.info(f"Skipped (not audio): '{subpath}'")
                continue

            logger.info(f"Loaded: '{subpath}'")
            yield (audio_bytes, subpath)
