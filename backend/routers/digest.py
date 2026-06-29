from collections import Counter
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from config import get_settings
from database import get_db
from models import Article, TopicWeight, User
from schemas import ArticleOut, DigestOut, StatusOut
from services.ranker import choose_diverse_articles, score_article
from tasks.pipeline import execute_pipeline, run_pipeline


router = APIRouter(prefix="/api", tags=["digest"])


def to_article_out(article: Article, score: float | None = None) -> ArticleOut:
    return ArticleOut(
        id=article.id,
        title=article.rewritten_title or article.title,
        summary=article.summary,
        url=article.url,
        source=article.source,
        topic=article.topic,
        reading_time_minutes=article.reading_time_minutes,
        score=score if score is not None else article.score,
    )


@router.get("/digest/today", response_model=DigestOut)
def get_today_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigestOut:
    settings = get_settings()
    cutoff = datetime.utcnow() - timedelta(hours=settings.FETCH_WINDOW_HOURS)
    articles = (
        db.execute(
            select(Article)
            .where(Article.published_at >= cutoff)
            .where(Article.is_representative.is_(True))
            .where(Article.shown_in_digest.is_(True))
            .order_by(Article.score.desc())
        )
        .scalars()
        .all()
    )

    if not articles:
        execute_pipeline()
        db.expire_all()
        articles = (
            db.execute(
                select(Article)
                .where(Article.published_at >= cutoff)
                .where(Article.is_representative.is_(True))
                .where(Article.shown_in_digest.is_(True))
                .order_by(Article.score.desc())
            )
            .scalars()
            .all()
        )

    weights = {
        row.topic: row.weight
        for row in db.execute(select(TopicWeight).where(TopicWeight.user_id == current_user.id)).scalars().all()
    }
    personalized_scores = {article.id: score_article(article, weights) for article in articles}
    articles = sorted(articles, key=lambda article: personalized_scores[article.id], reverse=True)

    if len(articles) > settings.MAX_ARTICLES_PER_DIGEST:
        articles = choose_diverse_articles(articles)

    breakdown = Counter(article.topic for article in articles)
    return DigestOut(
        date=date.today(),
        articles=[to_article_out(article, personalized_scores[article.id]) for article in articles],
        topic_breakdown=dict(breakdown),
    )


@router.post("/pipeline/run", response_model=StatusOut)
def start_pipeline() -> StatusOut:
    run_pipeline.delay()
    return StatusOut(status="started")
