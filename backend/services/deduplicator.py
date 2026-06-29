import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from config import get_settings
from models import Article


SOURCE_PRIORITY = {"Reuters": 0, "BBC News": 1, "Associated Press": 2}


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        self.parent[self.find(x)] = self.find(y)


def pick_representative(articles: list[Article]) -> Article:
    return min(
        articles,
        key=lambda article: (
            SOURCE_PRIORITY.get(article.source, 99),
            -len((article.summary or "").split()),
            article.published_at,
        ),
    )


def deduplicate_recent_articles(db: Session) -> int:
    settings = get_settings()
    cutoff = datetime.utcnow() - timedelta(hours=settings.FETCH_WINDOW_HOURS)
    articles = (
        db.execute(
            select(Article)
            .where(Article.published_at >= cutoff)
            .where(Article.embedding.is_not(None))
            .order_by(Article.published_at.desc())
        )
        .scalars()
        .all()
    )
    if not articles:
        return 0

    vectors = np.array([article.embedding for article in articles], dtype=np.float32)
    similarities = cosine_similarity(vectors)
    union_find = UnionFind(len(articles))

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if similarities[i][j] > settings.DEDUP_THRESHOLD:
                union_find.union(i, j)

    grouped_indexes: dict[int, list[int]] = defaultdict(list)
    for index in range(len(articles)):
        grouped_indexes[union_find.find(index)].append(index)

    for indexes in grouped_indexes.values():
        cluster_articles = [articles[index] for index in indexes]
        cluster_id = uuid.uuid4()
        representative = pick_representative(cluster_articles)
        for article in cluster_articles:
            article.cluster_id = cluster_id
            article.is_representative = article.id == representative.id

    db.commit()
    return len(grouped_indexes)
