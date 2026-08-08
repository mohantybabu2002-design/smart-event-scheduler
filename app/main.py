"""
App entry point.

Run with:  uvicorn app.main:app --reload
Then open: http://127.0.0.1:8000/docs
           (FastAPI auto-generates an interactive API testing page here)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth_routes, event_routes

# Creates all tables defined in models.py if they don't exist yet.
# (Fine for this stage of the project; once things get more serious
# you'd switch to Alembic migrations instead of this.)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Event Scheduler")

# CORS: by default, browsers block a webpage on one domain from calling
# an API on another domain, for security. Since our frontend (a static
# HTML file) is a separate "origin" from this API, we need to explicitly
# allow it. allow_origins=["*"] means "any website can call this API" --
# fine for a portfolio project; a real product would list specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(event_routes.router)


@app.get("/")
def root():
    return {"message": "Smart Event Scheduler API is running"}
