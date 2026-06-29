from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Article, TopicWeight, User, UserFeedback
from schemas import FeedbackIn, StatusOut


router = APIRouter(prefix="/api", tags=["articles"])


@router.post("/feedback", response_model=StatusOut)
async def submit_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatusOut:
    article = db.get(Article, payload.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    feedback = UserFeedback(
        user_id=current_user.id,
        article_id=article.id,
        feedback=payload.feedback,
        topic=article.topic,
    )
    db.add(feedback)

    topic_weight = db.execute(
        select(TopicWeight)
        .where(TopicWeight.user_id == current_user.id)
        .where(TopicWeight.topic == article.topic)
    ).scalar_one_or_none()
    if not topic_weight:
        topic_weight = TopicWeight(user_id=current_user.id, topic=article.topic, weight=1.0)
        db.add(topic_weight)

    multiplier = 1.1 if payload.feedback == "up" else 0.9
    topic_weight.weight = min(3.0, max(0.3, topic_weight.weight * multiplier))
    topic_weight.updated_at = datetime.utcnow()
    db.commit()

    return StatusOut(status="ok")


@router.get("/articles")
async def list_articles(db: Session = Depends(get_db)) -> list[dict]:
    articles = db.execute(select(Article).order_by(Article.published_at.desc()).limit(50)).scalars().all()
    return [
        {
            "id": article.id,
            "title": article.rewritten_title or article.title,
            "source": article.source,
            "topic": article.topic,
            "published_at": article.published_at,
            "is_representative": article.is_representative,
            "score": article.score,
        }
        for article in articles
    ]
