import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


RSS_FEEDS = [
    {"url": "https://feeds.feedburner.com/TechCrunch", "source": "TechCrunch", "topic_hint": "tech"},
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge", "topic_hint": "tech"},
    {"url": "https://hnrss.org/frontpage", "source": "Hacker News", "topic_hint": "tech"},
    {"url": "https://feeds.feedburner.com/ndtvnews-top-stories", "source": "NDTV", "topic_hint": "india"},
    {"url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "source": "Times of India", "topic_hint": "india"},
    {"url": "http://feeds.bbci.co.uk/news/rss.xml", "source": "BBC News", "topic_hint": "world"},
    {"url": "https://feeds.reuters.com/reuters/topNews", "source": "Reuters", "topic_hint": "world"},
    {"url": "https://www.sciencedaily.com/rss/top/science.xml", "source": "Science Daily", "topic_hint": "science"},
    {"url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "source": "NASA", "topic_hint": "science"},
    {"url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml", "source": "WSJ", "topic_hint": "business"},
]

TOPICS = ["tech", "india", "world", "science", "business", "sports", "health", "other"]


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/newsdash")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    ANTHROPIC_API_KEY: str | None = (
        None if os.getenv("ANTHROPIC_API_KEY") in (None, "", "your_key_here") else os.getenv("ANTHROPIC_API_KEY")
    )
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    DEDUP_THRESHOLD: float = float(os.getenv("DEDUP_THRESHOLD", "0.82"))
    MAX_ARTICLES_PER_DIGEST: int = int(os.getenv("MAX_ARTICLES_PER_DIGEST", "20"))
    MIN_ARTICLES_PER_DIGEST: int = int(os.getenv("MIN_ARTICLES_PER_DIGEST", "15"))
    MAX_ARTICLES_PER_TOPIC: int = int(os.getenv("MAX_ARTICLES_PER_TOPIC", "4"))
    FETCH_WINDOW_HOURS: int = int(os.getenv("FETCH_WINDOW_HOURS", "24"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
