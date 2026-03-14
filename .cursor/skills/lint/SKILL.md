---
name: lint
description: Runs Ruff and ty for pibot and fixes issues. Use when formatting code, fixing lint/type errors, or before committing. Ensures code matches project style and type rules.
---
# PiBot Lint and Types

## Commands

| Task        | Command                    |
|------------|----------------------------|
| Lint + fix | `uv run ruff check --fix` |
| Type check | `uv run ty`                |

Use `uv run` (not `uvx`) so project config and dev deps are used.

## Project config (pyproject.toml)

- **Line length**: 120
- **Paths**: `pyproject.toml`, `src/**/*.py`, `scripts/**/*.py`
- **Exclude**: `*/__init__.py` (for some rules)
- **Ruff**: E501, UP (pyupgrade), D (pydocstyle); ignore D203, D212
- **ty**: project default

## Workflow

1. `uv run ruff check --fix .` — fix what's auto-fixable; fix remaining by hand.
2. `uv run ty` — fix type errors.
3. Re-run to confirm clean.

Style: 2 spaces, camelCase, PascalCase, docstrings per Pydocstyle. See AGENTS.md for full conventions.
