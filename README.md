# AI Content Studio

Modular platform for generating, editing and publishing cinematic short-form content for multiple brands.

## First supported brand

**Cocoa Talk**

## Stack

- Python 3.12, uv
- FastAPI
- Ruff, MyPy, pytest

## Quickstart

```bash
uv sync
uv run uvicorn ai_content_studio.main:app --reload
```

## Dev

```bash
uv run pytest
uv run ruff check src/ tests/
uv run mypy
```

## Docker

```bash
docker build -t ai-content-studio .
docker run -p 8000:8000 ai-content-studio
```
