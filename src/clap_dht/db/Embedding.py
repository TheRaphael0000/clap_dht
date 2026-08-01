from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import VECTOR
from .Base import Base


class Embedding(Base):
    __tablename__ = 'embeddings'
    id = mapped_column(Integer, primary_key=True)
    path = mapped_column(String(500), unique=True)
    fingerprint = mapped_column(String(5000))
    embedding = mapped_column(VECTOR(512))
