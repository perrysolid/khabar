from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Article


@lru_cache
def get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    return get_model().encode(text).tolist()


def embed_missing_articles(db: Session) -> int:
    articles = db.execute(select(Article).where(Article.embedding.is_(None))).scalars().all()
    for article in articles:
        source_text = f"{article.title}. {(article.summary or '')[:200]}"
        article.embedding = embed_text(source_text)
    db.commit()
    return len(articles)
