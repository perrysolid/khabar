from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleOut(BaseModel):
    id: UUID
    title: str
    summary: str | None
    url: str
    source: str
    topic: str
    reading_time_minutes: int
    score: float


class DigestOut(BaseModel):
    date: date
    articles: list[ArticleOut]
    topic_breakdown: dict[str, int]


class FeedbackIn(BaseModel):
    article_id: UUID
    feedback: str = Field(pattern="^(up|down)$")


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: UUID
    email: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatusOut(BaseModel):
    status: str
