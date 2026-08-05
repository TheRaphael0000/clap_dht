from enum import Enum
import logging
from fastapi import FastAPI, Request
import uvicorn

from clap_dht.query import Query

logger = logging.getLogger("API")

app = FastAPI()

@app.get("/")
async def route_info():
    return "up"


class ProximityFunctions(str, Enum):
    max_inner_product="max_inner_product"
    cosine_distance="cosine_distance"
    l1_distance="l1_distance"


@app.get("/query/{external_id}")
async def route_query(request: Request, external_id: str, proximity: ProximityFunctions = ProximityFunctions.cosine_distance, limit: int = 100):
    query = Query(external_id=external_id, json=True, limit=limit, proximity_function=proximity.value)
    return query.get_json()


class API:
    def __init__(self, host, port, reload, no_dht):
        self.host = host        
        self.port = port
        self.reload = reload
        self.no_dht = no_dht

 
    def start(self):
        logger.debug(f"host={self.host}, port={self.port}, reload={self.reload}")
        uvicorn.run("clap_dht.serve.rest.api:app", host=self.host, port=self.port, reload=self.reload)