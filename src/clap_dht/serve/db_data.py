from clap_dht.db import DB
from clap_dht.query.query import Query


class DBDATA:

    def __ini__(self):
        pass

    def info(self):
        embeddings = Query.count()
        return {
            "db": {
                "embeddings": embeddings,
            }
        }