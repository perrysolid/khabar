import json
from datetime import datetime
from functools import lru_cache
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from config import get_settings
from models import Article


DIGEST_CACHE_KEY = "digest:latest"
PIPELINE_QUEUE_LOCK_KEY = "pipeline:refresh:queued"


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def article_to_cache(article: Article) -> dict:
    return {
        "id": str(article.id),
        "title": article.rewritten_title or article.title,
        "summary": article.summary,
        "url": article.url,
        "source": article.source,
        "topic": article.topic,
        "reading_time_minutes": article.reading_time_minutes,
        "score": article.score,
        "published_at": article.published_at.isoformat(),
    }


def cache_digest_articles(articles: list[Article]) -> None:
    settings = get_settings()
    payload = [article_to_cache(article) for article in articles]
    try:
        get_redis_client().set(DIGEST_CACHE_KEY, json.dumps(payload), ex=settings.DIGEST_CACHE_TTL_SECONDS)
    except RedisError as exc:
        print(f"Could not cache digest in Redis: {exc}")


def get_cached_digest_articles() -> list[dict]:
    try:
        raw = get_redis_client().get(DIGEST_CACHE_KEY)
    except RedisError as exc:
        print(f"Could not read digest cache from Redis: {exc}")
        return []
    if not raw:
        return []
    return json.loads(raw)


def should_queue_pipeline_refresh() -> bool:
    settings = get_settings()
    try:
        return bool(
            get_redis_client().set(
                PIPELINE_QUEUE_LOCK_KEY,
                datetime.utcnow().isoformat(),
                nx=True,
                ex=settings.PIPELINE_REFRESH_THROTTLE_SECONDS,
            )
        )
    except RedisError as exc:
        print(f"Could not acquire pipeline refresh lock in Redis: {exc}")
        return False


def parse_cached_uuid(value: str) -> UUID:
    return UUID(value)
