"""
App entry point.

Run with:  uvicorn app.main:app --reload
Then open: http://127.0.0.1:8000/docs
           (FastAPI auto-generates an interactive API testing page here)
"""

from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth_routes

# Creates all tables defined in models.py if they don't exist yet.
# (Fine for this stage of the project; once things get more serious
# you'd switch to Alembic migrations instead of this.)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Event Scheduler")

app.include_router(auth_routes.router)


@app.get("/")
def root():
    return {"message": "Smart Event Scheduler API is running"}
