import hashlib
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import get_settings
from models import Article


@lru_cache
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def simple_embed_text(text: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    magnitude = sum(value * value for value in vector) ** 0.5
    if not magnitude:
        return vector
    return [round(value / magnitude, 6) for value in vector]


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.EMBEDDING_BACKEND == "sentence-transformers":
        return get_model().encode(text).tolist()
    return simple_embed_text(text)


def embed_missing_articles(db: Session) -> int:
    articles = db.execute(select(Article).where(Article.embedding.is_(None))).scalars().all()
    for article in articles:
        source_text = f"{article.title}. {(article.summary or '')[:200]}"
        article.embedding = embed_text(source_text)
    db.commit()
    return len(articles)
