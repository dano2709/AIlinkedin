# AIlinkedin API

FastAPI service for the AIlinkedin Job Intelligence platform.

The API is intentionally small in Phase 1. It currently exposes system health and metadata while the domain and provider layers are built out incrementally.

## Run

~~~bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
~~~
