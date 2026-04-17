# PiBot – Agent Instructions

Instructions and context for AI agents working on this project.

## Code style

- **Indentation**: 2 spaces
- **Naming**: camelCase for variables/functions, PascalCase for classes
- **Linting/formatting**: Ruff (line length 120). Typical dev loop: `uv run ruff check --fix .`, then `uv run ruff format .`; for a no-fix pass use `uv run ruff check .`
- **Docstrings**: Pydocstyle (D) is enabled; exclude `*/__init__.py` from ruff

## Project structure

- Package root: `src/pibot/`. Entry point: `__main__.py`; core logic in `bot.py`, `database.py`, `errors.py`.
- **Cogs**: Add new features as cogs under `cogs/`; they are loaded in `bot.py`. Env-backed enums live in `pibot/settings.py` (``COMMAND_SYNC_BEHAVIOR``, ``ENABLE_DEV_TOOLS``); the bot stores ``commandSyncBehavior`` and ``enableDevTools`` from ``.from_env()`` at startup.

## Build & publish

Release artifacts:

1. **Docker image → Docker Hub and GHCR**
   - Build: `docker build -t pibot:local .` (local test) or use buildx for multi-arch.
   - Publish: `docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .` (Docker Hub; after `docker login`). On release, the same image is also pushed to `ghcr.io/<owner-lowercase>/pibot` (GitHub lowercases `github.repository` for the tag; e.g. `ghcr.io/tobiasgoetz/pibot`).
   - Consumers: `docker run --env-file .env tobiasgoetz/pibot` or `docker run --env-file .env ghcr.io/<owner-lowercase>/pibot:<tag>`.

2. **Python package → PyPI**
   - Build: `uv build` (uses `uv_build` backend per `pyproject.toml`).
   - Publish: `uv publish` (requires PyPI credentials/token).
   - Consumers install with `pip install pibot` or `uv add pibot` and run with `pibot`.

3. **Helm chart → GHCR (OCI)**
   - Chart lives in `charts/pibot/`; version is aligned with the app (combined versioning).
   - On release, `helm push` publishes to `oci://ghcr.io/<owner-lowercase>/helm-charts` (see `.github/workflows/helm-publish.yml`).
   - Install: `helm install <release-name> oci://ghcr.io/<owner-lowercase>/helm-charts/pibot --version <version>` (set env from Secret or values). Use `helm registry login ghcr.io` when the registry requires authentication.

Do not conflate Docker and PyPI; Helm chart publish runs on the same release and uses the app version from `pyproject.toml`.

Releases are automated with **Release Please**: conventional commits on `main` produce a Release PR (version bump in `pyproject.toml` only; no CHANGELOG.md). Merging that PR creates the tag, GitHub Release (with release notes), and triggers Docker Hub + GHCR (image), PyPI, and Helm chart (GHCR) publish. No direct push to `main` is required.

## Commands

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run bot | `uv run pibot` |
| Lint (fix auto-fixable) | `uv run ruff check --fix .` |
| Lint (report only) | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run ty check` (add `--fix` to apply fixes) |
| Regenerate API docs | `uv run --group docs sphinx-apidoc -f -o docs/source src/pibot` |
| Build HTML docs (strict) | `uv run --group docs sphinx-build -T -n -W -b html docs docs/_build/html` |
| Build package (sdist/wheel) | `uv build` |
| Publish to PyPI | `uv publish` |
| Docker build (local tag) | `docker build -t pibot:local .` |
| Docker run (local tag) | `docker run --env-file .env pibot:local` |
| Docker run (GHCR image) | `docker run --env-file .env ghcr.io/<owner-lowercase>/pibot:<tag>` |
| Docker publish (multi-arch; manual) | Via release; local: `docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .` (also tags `ghcr.io/<owner-lowercase>/pibot`) |
| Helm install (chart from GHCR OCI) | `helm install <release-name> oci://ghcr.io/<owner-lowercase>/helm-charts/pibot --version <version>` |

Ruff/`ty` config: `[tool.ruff]` and dev dependency group in `pyproject.toml`.

## Environment

- Config via `.env`; see `.env.example` for variables.
- Requires a Discord bot token and (for full features) MongoDB and DeepL API key.

## Conventions

- Prefer `uv run` for all Python/tool invocations in this repo.
- For active development, run with `uv run pibot`. Docker and PyPI are publish targets, not for day-to-day dev.
- Entry point is `pibot:run` (see `pyproject.toml`).
