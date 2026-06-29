# Personalised News Dashboard

A no-doom daily news dashboard: RSS ingestion, semantic deduplication, factual headline rewriting when an Anthropic key is available, ranking from feedback, and a compact React UI.

## Run With Docker

From this folder:

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:5174
- Backend health: http://localhost:8001/health
- Today's digest: http://localhost:8001/api/digest/today

The first digest request may take a while because it can fetch feeds, download the sentence-transformer model, embed articles, deduplicate them, and rank the first set.

## Anthropic

The app works without an Anthropic key. In that mode, it keeps original headlines and RSS summaries.

To enable rewriting:

```bash
export ANTHROPIC_API_KEY=your_real_key
docker compose up --build
```

## Manual Pipeline

Trigger a refresh:

```bash
curl -X POST http://localhost:8000/api/pipeline/run
curl -X POST http://localhost:8001/api/pipeline/run
```

Celery Beat also schedules the pipeline every 30 minutes.

## Backend Notes

The backend creates tables on startup for local convenience. The database schema matches the requested SQLAlchemy models:

- `articles`
- `user_feedback`
- `topic_weights`

## Useful Checks

```bash
curl http://localhost:8001/api/digest/today
curl -X POST http://localhost:8001/api/pipeline/run
docker compose logs -f backend celery_worker celery_beat
```
