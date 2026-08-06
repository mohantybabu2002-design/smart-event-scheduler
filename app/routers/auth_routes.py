"""
Auth routes: /signup, /login, /me

Kept in their own file (a "router") rather than main.py so the
project stays organized as it grows -- later we'll add
routers/events.py, routers/availability.py the same way.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=schemas.UserOut)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check email isn't already taken
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=user_in.name,
        email=user_in.email,
        password_hash=auth.hash_password(user_in.password),
        timezone=user_in.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # loads back the DB-generated id/created_at
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm expects fields named "username" and "password"
    # -- we treat "username" as the email here. This is what lets
    # FastAPI's auto-generated /docs page show a working login form.
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    """
    A protected route -- proves the auth system works end-to-end.
    Try calling this WITHOUT a token: you'll get 401.
    Call it WITH a valid token: you get your own user info back.
    """
    return current_user
