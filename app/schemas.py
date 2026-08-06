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
