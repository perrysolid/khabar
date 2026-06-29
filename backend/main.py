from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from database import Base, engine
from routers import articles, auth, digest


app = FastAPI(title="Personalised News Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    sync_auth_schema()
    Base.metadata.create_all(bind=engine)


def sync_auth_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as conn:
        if "topic_weights" in table_names:
            columns = {column["name"] for column in inspector.get_columns("topic_weights")}
            if "id" not in columns or "user_id" not in columns:
                conn.execute(text("DROP TABLE topic_weights"))

        if "user_feedback" in table_names:
            columns = {column["name"] for column in inspector.get_columns("user_feedback")}
            if "user_id" not in columns:
                conn.execute(text("DROP TABLE user_feedback"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(articles.router)
app.include_router(auth.router)
app.include_router(digest.router)
