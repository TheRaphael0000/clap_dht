from threading import Thread
import asyncio
from sqlalchemy import select

from clap_dht.db import DB, Embedding
from clap_dht.query.query import Query
from clap_dht.serve.dht_node import DHTNode
import io
import numpy as np
import umsgpack

import logging

from clap_dht.utils.consts import CLAP_EMBEDDING_SIZE, CLAP_MODEL

logger = logging.getLogger("DHTDB")



class DHTDB(DHTNode):

    def __init__(self):
        super().__init__()
        self.db = DB()
        self.running_tasks = set()
             
    async def start(self):
        await super().start()
        task = asyncio.create_task(self.publish_db())
        self.running_tasks.add(task)
        task.add_done_callback(self.running_tasks.discard)

    async def stop(self):
        await super().stop()

        
    async def info(self):
        infos = await super().info()
        return infos

    def pack_fingerprint(self, fingerprint):
        # use a list of tuple to be sure we pack in the same order
        return umsgpack.packb([
            ("model", CLAP_MODEL),
            ("fingerprint", fingerprint)
        ]).decode("latin-1")
    

    def pack_embedding(self, embedding):
        buffer = io.BytesIO()
        np.save(buffer, np.array(embedding), allow_pickle=False)
        return buffer.getvalue()
    

    def unpack_embedding(self, pack):
        try:
            array = np.load(pack, allow_pickle=False)
            print(array.shape, array.dtype)
            if array.shape == (CLAP_EMBEDDING_SIZE,):
                raise Exception("Invalid shape")
            return array
        except Exception as e:
            logger.error("Invalid embedding found \n{e}")


    async def publish_db(self):
        logger.info("publishing...")

        stmt = select(Embedding).execution_options(yield_per=100)
        with self.db as session:
            for embedding in session.scalars(stmt):
                await self.publish_embedding(embedding)
        logger.info("publishing finished")

        
    async def publish_embedding(self, embedding):
        key = self.pack_fingerprint(embedding.fingerprint)
        value = self.pack_embedding(embedding.embedding)

        values = await self.get_value(key)
        if values is None:
            return None
        for v in values:
            if v == value:
                logger.info(f"Already on the DHT: '{embedding.path}'")
                return

        await self.put_value(key, value)
        logger.info(f"Written on the DHT: '{embedding.path}'")


    async def query(self, fingerprint):
        key = self.pack_fingerprint(fingerprint)
        values = await self.get_value(key)
        if values is None:
            return None
        for v in values:
            try:
                return self.unpack_embedding(v)
            except Exception:
                pass
        return None
    