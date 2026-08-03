import json

from sqlalchemy import select

from clap_dht.db import DB, Embedding


class Query:
    proximity_functions = {
        "max_inner_product": (Embedding.embedding.max_inner_product, -1),
        "cosine_distance": (Embedding.embedding.cosine_distance, 1),
        "l1_distance": (Embedding.embedding.l1_distance, 1),
        # doesnt work but should according to the doc
        # "hamming_distance": Embedding.embedding.hamming_distance,
        # "jaccard_distance": Embedding.embedding.jaccard_distance,
    }

    def __init__(self, proximity_function, limit, json, path = None, external_id = None):
        self.db = DB()
        self.proximity_function = self.proximity_functions[proximity_function][0]
        self.order_by_factor = self.proximity_functions[proximity_function][1]
        self.limit = limit
        self.path = path
        self.json = json
        self.external_id = external_id

    def __str__(self):
        results = self.get()
        if self.json:
            output = [{"path": embedding.path, "external_id": embedding.external_id, "dist": dist} for embedding, dist in results]
            return json.dumps(output, indent=2)
        else:
            return "\n".join([f"{dist:4f} - '{embedding.path}'" for embedding, dist in results])


    def get(self):
        if self.path is not None:
            embedding = self.get_embedding_by_path(self.path)
        if self.external_id is not None:
            embedding = self.get_embedding_by_external_id(self.external_id)
        return self.query(embedding)


    def get_embedding_by_path(self, path):
        with self.db as session:
            return session.scalar(select(Embedding.embedding).where(Embedding.path == path))
        
    def get_embedding_by_external_id(self, external_id):
        with self.db as session:
            return session.scalar(select(Embedding.embedding).where(Embedding.external_id == external_id))
    
    def query(self, embedding):
        with self.db as session:
            distance_expr = self.proximity_function(embedding).label("metric")
            stmt = select(Embedding, distance_expr).filter(distance_expr > 0).order_by(self.order_by_factor * distance_expr).limit(self.limit)
            results = session.execute(stmt).all()
            return [r for r in results]