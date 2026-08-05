from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from .Base import Base

import logging
logger = logging.getLogger("DB")


class DB():
    def __init__(self):
        db_path = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
        self.engine = create_engine(db_path)
        self.session = Session(self.engine)
        

    def __enter__(self):
        return self.session.__enter__()
    
    def __exit__(self, *args):
        return self.session.__exit__(*args)

    
    def init(self, drop_all=False):
        logger.info("db initalization")
        with self as session:
            session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            session.commit()
        if drop_all:
            logger.info("db dropped")
            Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("db initialized")