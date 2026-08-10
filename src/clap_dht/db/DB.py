from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session

from clap_dht.utils.config import config
from .Base import Base

import logging
logger = logging.getLogger("DB")


class DB():
    def __init__(self):
        db_path = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}/{config.POSTGRES_DB}"
        self.engine = create_engine(db_path, connect_args={'connect_timeout': 2})
        self.session = Session(self.engine)
        try:
            self.test_connection()
            logger.info("Database connection succeeded")
        except Exception as e:
            logger.error(f"Database connection failed\n{e}")
            exit()

    def test_connection(self):
        with self as session:
            session.execute(text("SELECT 1"))

    def __enter__(self):
        return self.session.__enter__()
    
    def __exit__(self, *args):
        return self.session.__exit__(*args)

    def drop(self):
        Base.metadata.drop_all(self.engine)
        logger.info("Database dropped")

    def create(self):
        Base.metadata.create_all(self.engine)
        with self as session:
            session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            session.commit()
        logger.info("Database created")