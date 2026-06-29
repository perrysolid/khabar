import asyncio

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import TOPICS, get_settings
from models import Article


def fallback_article(article: Article) -> None:
    article.rewritten_title = article.rewritten_title or article.title
    article.summary = article.summary or "Summary unavailable."
    article.topic = article.topic if article.topic in TOPICS else "other"


async def ask(client: AsyncAnthropic, prompt: str) -> str:
    settings = get_settings()
    response = await client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=80,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


async def rewrite_one(client: AsyncAnthropic, article: Article) -> tuple[str, str, str]:
    headline_prompt = f"""Rewrite this news headline to be clear and factual.
Remove clickbait, urgency words, and emotional manipulation.
Keep it under 12 words. Return ONLY the rewritten headline, nothing else.

Original: {article.title}"""
    summary_prompt = f"""Write a 1-sentence factual summary of this article in plain English.
No opinion. No dramatic language. Under 25 words.
Return ONLY the summary sentence.

Title: {article.title}
Content: {(article.summary or '')[:500]}"""
    topic_prompt = f"""Classify this article into exactly one of these topics: {', '.join(TOPICS)}
Return ONLY the topic word, nothing else.

Title: {article.title}"""

    headline, summary, topic = await asyncio.gather(
        ask(client, headline_prompt),
        ask(client, summary_prompt),
        ask(client, topic_prompt),
    )
    topic = topic.lower().strip()
    if topic not in TOPICS:
        topic = "other"
    return headline, summary, topic


async def rewrite_missing_articles_async(db: Session, batch_size: int = 10) -> int:
    settings = get_settings()
    articles = (
        db.execute(
            select(Article)
            .where(Article.is_representative.is_(True))
            .where(Article.rewritten_title.is_(None))
            .order_by(Article.published_at.desc())
        )
        .scalars()
        .all()
    )
    if not articles:
        return 0

    if not settings.ANTHROPIC_API_KEY:
        for article in articles:
            fallback_article(article)
        db.commit()
        return len(articles)

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    processed = 0
    for start in range(0, len(articles), batch_size):
        batch = articles[start : start + batch_size]
        results = await asyncio.gather(*(rewrite_one(client, article) for article in batch), return_exceptions=True)
        for article, result in zip(batch, results, strict=False):
            if isinstance(result, Exception):
                print(f"Rewrite failed for {article.id}: {result}")
                fallback_article(article)
                continue
            article.rewritten_title, article.summary, article.topic = result
            processed += 1
        db.commit()
    return processed


def rewrite_missing_articles(db: Session) -> int:
    return asyncio.run(rewrite_missing_articles_async(db))
