"""
Pydantic schemas.

Models (models.py) define what's stored in the DB.
Schemas define what comes IN through the API (requests) and what
goes OUT (responses). They're deliberately different from the DB
model -- e.g. we NEVER return password_hash in a response, even
though it's a real column in the users table.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List
from app.models import ResponseStatus


class UserCreate(BaseModel):
    """What the client sends to POST /signup"""
    name: str
    email: EmailStr
    password: str
    timezone: str = "UTC"


class UserLogin(BaseModel):
    """What the client sends to POST /login"""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """What we send BACK -- notice: no password_hash field at all"""
    id: int
    name: str
    email: EmailStr
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True  # lets this read directly from a SQLAlchemy object


class Token(BaseModel):
    """What we send back after a successful login"""
    access_token: str
    token_type: str = "bearer"


# ---------- Events ----------

class EventCreate(BaseModel):
    """What the client sends to POST /events"""
    title: str
    start_time: datetime  # client sends in UTC (ISO format, e.g. "2026-08-10T14:00:00Z")
    end_time: datetime
    participant_ids: List[int] = []  # other users to invite, besides the host


class ParticipantOut(BaseModel):
    user_id: int
    name: str
    response_status: ResponseStatus

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    id: int
    host_id: int
    title: str
    start_time: datetime
    end_time: datetime
    participants: List[ParticipantOut] = []

    class Config:
        from_attributes = True


# ---------- Common free-time finder ----------

class FreeSlotRequest(BaseModel):
    """What the client sends to find a shared free slot across a group."""
    user_ids: List[int]  # everyone who needs to be free -- include yourself if relevant
    range_start: datetime
    range_end: datetime
    min_duration_minutes: int = 30


class FreeSlotOut(BaseModel):
    start_time: datetime
    end_time: datetime


