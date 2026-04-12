from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# NOTE: Replace this string with your actual Render Database URL when deploying.
# For local testing right now, we will use a lightweight SQLite database.
SQLALCHEMY_DATABASE_URL = "sqlite:///./pocketwise.db"
# Example of a Render Postgres URL: "postgresql://user:password@hostname/dbname"

# The connect_args dictionary is only needed for SQLite. Remove it when switching to Postgres.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
