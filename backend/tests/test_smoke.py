import os
import sys
from types import ModuleType, SimpleNamespace

from fastapi.testclient import TestClient


os.environ["DATABASE_URL"] = "sqlite:///./smoke-test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET_KEY"] = "smoke-test-secret"


class FakeCelery:
    def __init__(self, *args, **kwargs) -> None:
        self.conf = SimpleNamespace(beat_schedule={}, timezone="UTC")

    def task(self, *args, **kwargs):
        def decorator(func):
            func.delay = lambda *delay_args, **delay_kwargs: func(*delay_args, **delay_kwargs)
            return func

        return decorator


def install_import_stubs() -> None:
    celery = ModuleType("celery")
    celery.Celery = FakeCelery
    sys.modules.setdefault("celery", celery)

    feedparser = ModuleType("feedparser")
    feedparser.parse = lambda *args, **kwargs: SimpleNamespace(entries=[], bozo=False)
    sys.modules.setdefault("feedparser", feedparser)

    sentence_transformers = ModuleType("sentence_transformers")
    sentence_transformers.SentenceTransformer = lambda *args, **kwargs: SimpleNamespace(
        encode=lambda text: SimpleNamespace(tolist=lambda: [])
    )
    sys.modules.setdefault("sentence_transformers", sentence_transformers)

    anthropic = ModuleType("anthropic")
    anthropic.AsyncAnthropic = object
    sys.modules.setdefault("anthropic", anthropic)

    numpy = ModuleType("numpy")
    numpy.float32 = float
    numpy.array = lambda values, dtype=None: values
    sys.modules.setdefault("numpy", numpy)

    sklearn = ModuleType("sklearn")
    metrics = ModuleType("sklearn.metrics")
    pairwise = ModuleType("sklearn.metrics.pairwise")
    pairwise.cosine_similarity = lambda vectors: []
    sys.modules.setdefault("sklearn", sklearn)
    sys.modules.setdefault("sklearn.metrics", metrics)
    sys.modules.setdefault("sklearn.metrics.pairwise", pairwise)


install_import_stubs()

from main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
