import os
import pathlib

from sqlalchemy import exists, select
import filetype

from torch.utils.data import IterableDataset

from clap_dht.db import DB, Embedding
from clap_dht.utils import logger


class AudioBytesDataset(IterableDataset):
    def __init__(self, root_dir, force_process):
        self.root_dir = root_dir
        self.db = DB()
        self.force_process = force_process

    def __iter__(self):
        for fullpath in pathlib.Path(self.root_dir).rglob("*"):
            subpath = str(fullpath.relative_to(self.root_dir))
            fullpath = str(fullpath)

            if not os.path.isfile(fullpath):
                continue

            if not self.force_process:
                with self.db as session:
                    is_exist = session.scalar(select(exists().where(Embedding.path == subpath)))
                if is_exist:
                    logger.info(f"Skipped (already in db): '{subpath}'")
                    continue

            audio_bytes = open(fullpath, "rb").read()

            kind = filetype.guess(audio_bytes)
            if kind is None or not kind.mime.startswith("audio"):
                logger.info(f"Skipped (not audio): '{subpath}'")
                continue

            logger.info(f"Loaded: '{subpath}'")
            yield (audio_bytes, subpath)
