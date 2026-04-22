from app.workers.celery_app import celery_app
from app.workers.analyze_tasks import analyze_import  # noqa: F401
from app.workers.transform_tasks import transform_import  # noqa: F401


@celery_app.task(name="workers.ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "worker": "ready"}
