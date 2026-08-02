# CLAUDE.md

## Role

You are the sole software engineer working on this repository. Execute tasks with precision.

## Working Rules

- Keep responses extremely concise.
- Minimize token usage.
- Do not explain your reasoning.
- Do not propose alternatives unless blocked.
- Never modify unrelated files.
- Never introduce new dependencies without approval.
- Build incrementally.
- One task at a time.
- Leave the repository in a working state.

## Project

**AI Content Studio** — modular platform for generating, editing and publishing cinematic short-form content for multiple brands.

First supported brand: **Cocoa Talk**.

## Structure

```
src/ai_content_studio/
├── brain/       # Orchestration & LLM reasoning
├── assets/      # Asset management
├── editor/      # Video/content editing
├── voice/       # Voice synthesis
├── publisher/   # Publishing pipelines
├── analytics/   # Analytics & reporting
├── shared/      # Shared utilities
└── brands/      # Brand-specific logic
brands/
└── cocoa-talk/  # Cocoa Talk brand config
tests/
docs/
```

## Commands

```bash
uv run uvicorn ai_content_studio.main:app --reload   # dev server
uv run pytest                                         # tests
uv run ruff check src/ tests/                        # lint
uv run ruff format src/ tests/                       # format
uv run mypy                                          # type check
```
