import asyncio

from src.clap_dht.db import DB

from .db import Embedding
from sqlalchemy import select

db = DB()


async def query(id, limit=100):
    with db as session:
        target = session.scalar(select(Embedding.embedding).where(Embedding.id == id))
        distance = Embedding.embedding.cosine_distance(target).label("dist")
        results = session.query(Embedding, distance).where(Embedding.id != id).order_by(distance).limit(limit).all()
        return results


async def main():

    for r,d in await query(1):
        print(r.id, d, r.path)


asyncio.run(main())

        