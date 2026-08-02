from sqlalchemy import Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import VECTOR
from .Base import Base


class Embedding(Base):
    __tablename__ = 'embeddings'
    path = mapped_column(String(500), primary_key=True)
    external_id = mapped_column(String(50))
    fingerprint = mapped_column(LargeBinary())
    embedding = mapped_column(VECTOR(512))
    remove_flag = mapped_column(Boolean())
