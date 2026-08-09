"""
Database models (tables).

users        -- who can log in
events       -- a meeting/booking, owned by one user (the host)
participants -- links events to the other users invited to them
               (many-to-many between events and users, with extra
               data attached: response_status)
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


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

    # events this user is hosting
    hosted_events = relationship("Event", back_populates="host")


class ResponseStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)

    # ALWAYS stored in UTC -- this is the golden rule for scheduling apps.
    # We convert to each user's local timezone only when displaying.
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    host = relationship("User", back_populates="hosted_events")
    participants = relationship(
        "Participant", back_populates="event", cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    response_status = Column(
        Enum(ResponseStatus), default=ResponseStatus.pending, nullable=False
    )

    event = relationship("Event", back_populates="participants")
    user = relationship("User")

    @property
    def name(self):
        """Lets the API return the participant's name without a separate lookup."""
        return self.user.name if self.user else None

