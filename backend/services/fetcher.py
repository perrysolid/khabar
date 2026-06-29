import re
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import RSS_FEEDS
from models import Article


TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = TAG_RE.sub(" ", value)
    return " ".join(without_tags.split())


def estimate_reading_time(*parts: str) -> int:
    word_count = sum(len(part.split()) for part in parts if part)
    return max(1, word_count // 200)


def parse_date(entry) -> datetime:
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            return parsedate_to_datetime(raw).replace(tzinfo=None)
        except (TypeError, ValueError, AttributeError):
            continue
    return datetime.utcnow()


def fetch_feeds(db: Session) -> list:
    new_ids = []
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed["url"])
        if getattr(parsed, "bozo", False) and not parsed.entries:
            print(f"[{datetime.utcnow().isoformat()}] Skipping malformed feed: {feed['source']}")
            continue

        for entry in parsed.entries:
            url = entry.get("link")
            title = clean_text(entry.get("title"))
            if not url or not title:
                continue

            exists = db.execute(select(Article.id).where(Article.url == url)).scalar_one_or_none()
            if exists:
                continue

            summary = clean_text(entry.get("summary") or entry.get("description"))
            article = Article(
                title=title,
                summary=summary or None,
                url=url,
                source=feed["source"],
                topic=feed["topic_hint"],
                reading_time_minutes=estimate_reading_time(title, summary),
                published_at=parse_date(entry),
                is_representative=False,
                shown_in_digest=False,
            )
            db.add(article)
            db.flush()
            new_ids.append(article.id)

    db.commit()
    return new_ids
