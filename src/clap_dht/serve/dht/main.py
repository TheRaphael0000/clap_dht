import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
import opendht.aio as dht
import base64
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DHT")

dht_node = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global dht_node
    logger.info("Starting DHT Node...")

    bootstrap_host, bootstrap_port = os.getenv("DHT_BOOTSTRAP").split(":")
    network = int(os.getenv("DHT_NETWORK"))

    logger.info(f"bootstrap: {bootstrap_host}:{bootstrap_port}")
    logger.info(f"network: {network}")

    dht_node = dht.DhtRunner()
    dht_node.bootstrap(bootstrap_host, bootstrap_port)

    config = dht.DhtConfig()
    config.setMaintainStorage(True)
    config.setNetwork(network)

    dht_node.run(config=config)

    logger.info(f"node id: {dht_node.getNodeId()}")

    yield

    logger.info("Shutting down DHT Node...")
    if dht_node:
        await dht_node.shutdown()
        logger.info("DHT Node shut down successfully.")


app = FastAPI(
    lifespan=lifespan
)


@app.get("/")
async def info():
    try:
        return {
            "isRunning": dht_node.isRunning(),
            "StorageLog": dht_node.getStorageLog().replace("\n", ""),
            "Network": os.getenv("DHT_NETWORK"),
            "Bootstrap": os.getenv("DHT_BOOTSTRAP"),
        }
    except Exception as e:
        logger.error(e)
        return {}


@app.post("/key/{key}")
async def put_value(request: Request, key: str):
    try:
        body = await request.body()
        key_hash = dht.InfoHash.get(key)
        dht_value = dht.Value(body)
        await dht_node.put(key_hash, dht_value, permanent=True)
        return Response()
    except Exception as e:
        logger.error(f"Failed to put data into DHT: {e}")
        raise HTTPException(status_code=500, detail=f"DHT Error: {str(e)}")


@app.get("/key/{key}")
async def get_value(key: str):
    try:
        key_hash = dht.InfoHash.get(key)
        results = await dht_node.getAll(key_hash)
        values = []
        for val in results:
            values.append(base64.b64encode(val.data))
        return values
    except Exception as e:
        logger.error(f"Failed to get data from DHT: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
