import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import opendht.aio as dht

from clap_dht.utils.config import config

logger = logging.getLogger("DHT")


class DHTNode:
    def __init__(self):
        logger.info("initializing")

        self.bootstrap_host, self.bootstrap_port = config.DHT_BOOTSTRAP.split(":")
        self.network = int(config.DHT_NETWORK)

        logger.info(f"bootstrap: {self.bootstrap_host}:{self.bootstrap_port}")
        logger.info(f"network: {self.network}")
        
        self.config = dht.DhtConfig()
        self.config.setMaintainStorage(True)
        self.config.setNetwork(self.network)

    async def start(self):
        logger.info("Starting DHT Node...")

        self.dht_runner = dht.DhtRunner()
        self.dht_runner.bootstrap(self.bootstrap_host, self.bootstrap_port)

        self.dht_runner.run(config=self.config)
        logger.info(f"node id: {self.dht_runner.getNodeId()}")

    async def stop(self):
        logger.info("Shutting down DHT Node...")
        if self.dht_runner:
            await self.dht_runner.shutdown()
            logger.info("DHT Node shut down successfully.")


    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.start()
        yield
        await self.stop()


    async def info(self):
        try:
            return { 
            "dht": {
                    "isRunning": self.dht_runner.isRunning(),
                    "StorageLog": [l for l in self.dht_runner.getStorageLog().split("\n") if len(l) > 0][-1],
                    "Network": self.network,
                    "Node ID": str(self.dht_runner.getNodeId()),
                    "Bootstrap": f"{self.bootstrap_host}:{self.bootstrap_port}",
                }
            }
        except Exception as e:
            logger.error(e)
            return {}


    async def put_value(self, key: str, value: bytes):
        try:
            key_hash = dht.InfoHash.get(key)
            logger.debug(f"Putting {key_hash}")
            dht_value = dht.Value(value)
            await self.dht_runner.put(key_hash, dht_value, permanent=True)
        except Exception as e:
            logger.error(e)
            raise e


    async def get_value(self, key: bytes):
        try:
            key_hash = dht.InfoHash.get(key)
            logger.debug(f"Getting {key_hash}")
            results = await self.dht_runner.getAll(key_hash)
            values = []
            for val in results:
                values.append(val.data)
            return values
        except Exception as e:
            logger.error(e)
            raise e
