"""
Database connection setup.

We use SQLAlchemy as the ORM (Object-Relational Mapper) — it lets us
write Python classes instead of raw SQL for most operations, while
still letting us drop to raw SQL when we need to (e.g. for the
overlap-detection queries later).
"""

import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Reads from environment variable so we never hardcode secrets/URLs.
# Locally this points to your Postgres instance; in production
# (Render/Railway) it's set automatically or via their dashboard.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/scheduler"
)

engine = create_engine(DATABASE_URL)

# Each request gets its own DB session (a "conversation" with the DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our model classes (User, Event, etc.) will inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: opens a DB session for a request,
    hands it to the route function, then closes it afterward
    -- even if the route raised an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
