from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import create_access_token, get_password_hash, verify_password
from config import TOPICS
from database import get_db
from models import TopicWeight, User
from schemas import TokenOut, UserCreate


router = APIRouter(prefix="/auth", tags=["auth"])


def seed_topic_weights(db: Session, user: User) -> None:
    for topic in TOPICS:
        db.add(TopicWeight(user_id=user.id, topic=topic, weight=1.0, updated_at=datetime.utcnow()))


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    email = payload.email.strip().lower()
    existing_user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(email=email, hashed_password=get_password_hash(payload.password))
    db.add(user)
    db.flush()
    seed_topic_weights(db, user)
    db.commit()
    db.refresh(user)

    return TokenOut(access_token=create_access_token(user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    email = payload.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenOut(access_token=create_access_token(user))
