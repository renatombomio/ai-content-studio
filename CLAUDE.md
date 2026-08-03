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

**Cocoa Talk Studio** — a purpose-built editorial content platform for the Cocoa Talk brand.

Cocoa Talk is not a generic AI video generator.
It is an introspective content brand. Technology serves the brand. The brand drives every technical decision.

First and only supported brand: **Cocoa Talk**.

## Brand Awareness

Before implementing any feature, ask: does this serve the Cocoa Talk editorial identity?

The brand is defined in:

- `docs/BRAND.md` — editorial bible
- `docs/COCO.md` — mascot reference
- `brands/cocoa-talk/` — brand assets and configuration

## Structure

```
src/ai_content_studio/
├── app.py
├── core/
├── brain/
├── assets/
├── video/
├── publisher/
├── scheduler/
├── storage/
├── shared/
└── brands/
brands/
└── cocoa-talk/
docs/
tests/
```

## Commands

```bash
uv run uvicorn ai_content_studio.app:app --reload   # dev server
uv run pytest                                        # tests
uv run ruff check src/ tests/                       # lint
uv run ruff format src/ tests/                      # format
uv run mypy                                         # type check
```

---

# Development Contract

This repository follows a strict implementation workflow.

## Source of Truth

The following documents are authoritative:

- docs/ROADMAP.md
- docs/ARCHITECTURE.md
- docs/PIPELINE.md
- docs/BRAND.md
- docs/COCO.md

If implementation differs from these documents, align the implementation.

Do not rewrite these documents unless explicitly requested.

---

## Architecture

The architecture is frozen.

Do not:

- rename modules
- move packages
- create new top-level packages
- remove existing packages
- change module responsibilities

If an architectural change appears necessary, STOP and explain why.

Never implement architectural changes without explicit approval.

---

## Scope

Implement only the requested task.

Do not implement future tasks.

Do not add "nice to have" features.

Do not anticipate future requirements.

---

## Dependencies

Do not introduce new dependencies without approval.

Prefer the existing stack whenever possible.

---

## Coding Style

Keep implementations small.

Prefer readable code over clever code.

Avoid unnecessary abstractions.

Avoid premature optimization.

---

## Testing

Every completed task must leave the repository in a working state.

Before finishing a task always run:

- pytest
- ruff check
- mypy

---

## Responses

Keep responses concise.

Return only:

- files changed
- validation results
- suggested commit message

Do not explain implementation unless requested.
