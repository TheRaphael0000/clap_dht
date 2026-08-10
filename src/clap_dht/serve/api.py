from enum import Enum
import logging
from fastapi import FastAPI, HTTPException, Request
import uvicorn

from clap_dht.db import DB
from clap_dht.query import Query
from clap_dht.serve.dht_db import DHTDB

logger = logging.getLogger("API")


class ProximityFunctions(str, Enum):
    max_inner_product="max_inner_product"
    cosine_distance="cosine_distance"
    l1_distance="l1_distance"

def create_app(with_dht):
    if with_dht:
        dht_node = DHTDB()
        app = FastAPI(lifespan=dht_node.lifespan)
    else:
        dht_node = None
        app = FastAPI()

    @app.get("/")
    async def route_info():
        info = {
            "up": True
        }
        if dht_node:
            info["dht"] = await dht_node.info()
        
        return info


    @app.get("/query/{external_id}")
    async def route_query(request: Request, external_id: str, proximity: ProximityFunctions = ProximityFunctions.cosine_distance, limit: int = 100):
        try:
            query = Query(external_id=external_id, json=True, limit=limit, proximity_function=proximity.value)
            result = query.get_json()
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))
        return result

    return app, dht_node


class API:
    def __init__(self, host, port, no_dht):
        DB() # to ensure connection to the db before starting the app
        self.host = host
        self.port = port
        self.no_dht = no_dht
        self.app, self.dht_node = create_app(not self.no_dht)

 
    def start(self):
        logger.debug(f"host={self.host}, port={self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)