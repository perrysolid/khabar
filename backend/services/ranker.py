from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import get_settings
from models import Article


def score_article(article: Article, topic_weights: dict[str, float]) -> float:
    now = datetime.utcnow()
    age_hours = max(0.0, (now - article.published_at).total_seconds() / 3600)
    recency = max(0.0, 1 - (age_hours / 24))
    topic_weight = topic_weights.get(article.topic, 1.0)
    score = 1.0 * (0.5 + 0.5 * recency) * topic_weight
    return min(1.0, round(score, 4))


def choose_diverse_articles(articles: list[Article]) -> list[Article]:
    settings = get_settings()
    selected: list[Article] = []
    counts: Counter[str] = Counter()

    for article in articles:
        if len(selected) >= settings.MAX_ARTICLES_PER_DIGEST:
            break
        if counts[article.topic] >= settings.MAX_ARTICLES_PER_TOPIC:
            continue
        selected.append(article)
        counts[article.topic] += 1

    if len(selected) < settings.MIN_ARTICLES_PER_DIGEST:
        selected_ids = {article.id for article in selected}
        relaxed_limit = settings.MAX_ARTICLES_PER_TOPIC + 1
        for article in articles:
            if len(selected) >= settings.MAX_ARTICLES_PER_DIGEST:
                break
            if article.id in selected_ids or counts[article.topic] >= relaxed_limit:
                continue
            selected.append(article)
            selected_ids.add(article.id)
            counts[article.topic] += 1

    return selected


def score_and_mark_digest(db: Session) -> list[Article]:
    settings = get_settings()
    cutoff = datetime.utcnow() - timedelta(hours=settings.FETCH_WINDOW_HOURS)
    weights: dict[str, float] = {}
    articles = (
        db.execute(
            select(Article)
            .where(Article.published_at >= cutoff)
            .where(Article.is_representative.is_(True))
        )
        .scalars()
        .all()
    )

    for article in articles:
        article.score = score_article(article, weights)
        article.shown_in_digest = False

    ranked = sorted(articles, key=lambda article: article.score, reverse=True)
    selected = choose_diverse_articles(ranked)
    for article in selected:
        article.shown_in_digest = True

    db.commit()
    return selected
