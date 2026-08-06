"""
Database models (tables).

Right now: just User. We'll add Event, Availability, Participant
in the next step once auth is working end-to-end.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # IMPORTANT for a scheduler: every user has a timezone.
    # We store all event times in UTC in the DB, and convert
    # to/from this timezone only when displaying to the user.
    # e.g. "Asia/Kolkata", "America/New_York"
    timezone = Column(String, default="UTC", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
