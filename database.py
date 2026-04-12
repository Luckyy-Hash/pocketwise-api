from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql://pocketwise_db_user:qrQ8eIX0dP1Eo9g1w8CHqQCBs2fXT84Y@dpg-d7e1nscvikkc73efjq7g-a.oregon-postgres.render.com/pocketwise_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
