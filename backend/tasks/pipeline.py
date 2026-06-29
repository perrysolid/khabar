from datetime import datetime

from celery import Celery

from config import get_settings
from database import Base, SessionLocal, engine
from services.deduplicator import deduplicate_recent_articles
from services.embedder import embed_missing_articles
from services.fetcher import fetch_feeds
from services.ranker import score_and_mark_digest
from services.rewriter import rewrite_missing_articles


settings = get_settings()
celery_app = Celery("news_dashboard", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
app = celery_app

celery_app.conf.beat_schedule = {
    "run-pipeline": {
        "task": "tasks.pipeline.run_pipeline",
        "schedule": 1800.0,
    },
}
celery_app.conf.timezone = "UTC"


def log(message: str) -> None:
    print(f"[{datetime.utcnow().isoformat()}] {message}")


def execute_pipeline() -> dict[str, int]:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        log("Pipeline started.")
        new_article_ids = fetch_feeds(db)
        log(f"Fetched {len(new_article_ids)} new articles.")

        embedded_count = embed_missing_articles(db)
        log(f"Generated {embedded_count} embeddings.")

        cluster_count = deduplicate_recent_articles(db)
        log(f"Built {cluster_count} clusters.")

        rewritten_count = rewrite_missing_articles(db)
        log(f"Rewrote or filled {rewritten_count} representative articles.")

        digest_articles = score_and_mark_digest(db)
        log(
            "Pipeline complete. "
            f"{len(new_article_ids)} new articles. "
            f"{cluster_count} clusters. "
            f"{len(digest_articles)} shown in digest."
        )
        return {
            "new_articles": len(new_article_ids),
            "clusters": cluster_count,
            "shown_in_digest": len(digest_articles),
        }
    finally:
        db.close()


@celery_app.task(name="tasks.pipeline.run_pipeline")
def run_pipeline() -> dict[str, int]:
    return execute_pipeline()
