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
from services.digest_cache import get_cached_digest_articles, parse_cached_uuid, should_queue_pipeline_refresh
from services.ranker import choose_diverse_articles, score_article
from tasks.pipeline import run_pipeline


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


def cached_article_score(article: dict, topic_weights: dict[str, float]) -> float:
    published_at = datetime.fromisoformat(article["published_at"])
    age_hours = max(0.0, (datetime.utcnow() - published_at).total_seconds() / 3600)
    recency = max(0.0, 1 - (age_hours / 24))
    topic_weight = topic_weights.get(article["topic"], 1.0)
    return min(1.0, round((0.5 + 0.5 * recency) * topic_weight, 4))


def cached_article_to_out(article: dict, score: float) -> ArticleOut:
    return ArticleOut(
        id=parse_cached_uuid(article["id"]),
        title=article["title"],
        summary=article["summary"],
        url=article["url"],
        source=article["source"],
        topic=article["topic"],
        reading_time_minutes=article["reading_time_minutes"],
        score=score,
    )


def queue_pipeline_refresh() -> None:
    try:
        if should_queue_pipeline_refresh():
            run_pipeline.delay()
    except Exception as exc:
        print(f"Could not queue pipeline refresh: {exc}")


@router.get("/digest/today", response_model=DigestOut)
def get_today_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigestOut:
    settings = get_settings()
    cutoff = datetime.utcnow() - timedelta(hours=settings.FETCH_WINDOW_HOURS)
    weights = {
        row.topic: row.weight
        for row in db.execute(select(TopicWeight).where(TopicWeight.user_id == current_user.id)).scalars().all()
    }

    cached_articles = get_cached_digest_articles()
    if cached_articles:
        queue_pipeline_refresh()
        scored = [(article, cached_article_score(article, weights)) for article in cached_articles]
        scored = sorted(scored, key=lambda item: item[1], reverse=True)[: settings.MAX_ARTICLES_PER_DIGEST]
        breakdown = Counter(article["topic"] for article, _score in scored)
        return DigestOut(
            date=date.today(),
            articles=[cached_article_to_out(article, score) for article, score in scored],
            topic_breakdown=dict(breakdown),
        )

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
        queue_pipeline_refresh()
        articles = (
            db.execute(
                select(Article)
                .where(Article.published_at >= cutoff)
                .order_by(Article.published_at.desc())
                .limit(settings.MAX_ARTICLES_PER_DIGEST * 3)
            )
            .scalars()
            .all()
        )
    else:
        queue_pipeline_refresh()

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
