from fastapi import FastAPI

from .settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="LinkedIn Job Intelligence API",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/v1/meta", tags=["system"])
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "foundation",
    }
