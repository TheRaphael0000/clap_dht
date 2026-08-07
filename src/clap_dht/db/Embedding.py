from sqlalchemy import String, Boolean, LargeBinary
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import VECTOR

from clap_dht.utils.consts import CLAP_EMBEDDING_SIZE

from .Base import Base


class Embedding(Base):
    __tablename__ = 'embeddings'
    path = mapped_column(String(500), primary_key=True)
    external_id = mapped_column(String(50), index=True)
    fingerprint = mapped_column(LargeBinary())
    embedding = mapped_column(VECTOR(CLAP_EMBEDDING_SIZE))
    # from_dht = mapped_column(Boolean())
    remove_flag = mapped_column(Boolean())
