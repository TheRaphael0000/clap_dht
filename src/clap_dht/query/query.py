import json

from sqlalchemy import select
from pgvector.sqlalchemy import avg

from clap_dht.db import DB, Embedding
import logging


logger = logging.getLogger("QUERY")


class Query:
    proximity_functions = {
        "max_inner_product": (Embedding.embedding.max_inner_product, -1),
        "cosine_distance": (Embedding.embedding.cosine_distance, 1),
        "l1_distance": (Embedding.embedding.l1_distance, 1),
        # doesnt work but should according to the doc
        # "hamming_distance": Embedding.embedding.hamming_distance,
        # "jaccard_distance": Embedding.embedding.jaccard_distance,
    }

    def __init__(self, proximity_function, limit, json, path = None, songId = None, albumId = None, artistId = None):
        logger.debug(f"Query created proximity_function={proximity_function} limit={limit} json={json} path={path} songId={songId} albumId={albumId} artistId={artistId}")
        self.db = DB()
        self.proximity_function = self.proximity_functions[proximity_function][0]
        self.order_by_factor = self.proximity_functions[proximity_function][1]
        self.limit = limit
        self.path = path
        self.json = json
        self.songId = songId
        self.albumId = albumId
        self.artistId = artistId

    def __str__(self):
        if self.json:
            return json.dumps(self.get_json(), indent=2)
        else:
            return "\n".join(self.get_text())

    def get_text(self):
        results = self.get()
        output = [f"{score:4f} - '{embedding.path}'" for embedding, score in results]
        return output

    def get_json(self):
        results = self.get()
        output = [{"path": embedding.path, "songId": embedding.songId, "score": score} for embedding, score in results]
        return output

    def get(self):
        if self.path is not None:
            embedding = self.get_embedding_by_path(self.path)
        if self.songId is not None:
            embedding = self.get_embedding_by_songId(self.songId)
        if self.albumId is not None:
            embedding = self.get_embedding_by_albumId(self.albumId)
        if self.artistId is not None:
            embedding = self.get_embedding_by_artistId(self.artistId)
        if embedding is None:
            raise Exception("Embedding not found")
        results = self.query_similar(embedding)
        return results


    def get_embedding_by_path(self, path):
        with self.db as session:
            return session.scalar(select(Embedding.embedding).where(Embedding.path == path))
        
    def get_embedding_by_songId(self, songId):
        with self.db as session:
            return session.scalar(select(Embedding.embedding).where(Embedding.songId == songId))

    def get_embedding_by_albumId(self, albumId):
        with self.db as session:
            return session.scalar(select(avg(Embedding.embedding)).where(Embedding.albumId == albumId))
        
    def get_embedding_by_artistId(self, artistId):
        with self.db as session:
            return session.scalar(select(avg(Embedding.embedding)).where(Embedding.artistId == artistId))
    
    def query_similar(self, embedding):
        with self.db as session:
            proximity_expr = self.proximity_function(embedding).label("metric")
            stmt = select(Embedding, proximity_expr).filter(proximity_expr > 0).order_by(self.order_by_factor * proximity_expr).limit(self.limit)
            results = session.execute(stmt).all()
            return [r for r in results]

    @staticmethod
    def count():
        with DB() as session:
            return session.query(Embedding.path).count()