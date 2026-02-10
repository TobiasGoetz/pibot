# PiBot – Agent Instructions

Instructions and context for AI agents working on this project.

## Code Style

- **Indentation**: 2 spaces
- **Naming**: camelCase for variables/functions, PascalCase for classes
- **Linting/formatting**: Ruff (line length 120). Run: `uv run ruff check .` and `uv run ruff format .`
- **Docstrings**: Pydocstyle (D) is enabled; exclude `*/__init__.py` from ruff

## Project Structure

- Package root: `src/pibot/`. Entry point: `__main__.py`; core logic in `bot.py`, `database.py`, `errors.py`.
- **Cogs**: Add new features as cogs under `cogs/`; they are loaded in `bot.py`. The DevTools cog loads only when `ENVIRONMENT` is not `production` or `testing`.

## Build & Publish (two distribution paths)

The project is built and published in two ways:

1. **Docker image → Docker Hub and GHCR**
   - Build: `docker build -t pibot:local .` (local test) or use buildx for multi-arch.
   - Publish: `docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .` (Docker Hub; after `docker login`). On release, the same image is also pushed to `ghcr.io/<owner>/pibot`.
   - Consumers run the bot via the image (e.g. `docker run --env-file .env tobiasgoetz/pibot` or `ghcr.io/<owner>/pibot`).

2. **Python package → PyPI**
   - Build: `uv build` (uses `uv_build` backend per `pyproject.toml`).
   - Publish: `uv publish` (requires PyPI credentials/token).
   - Consumers install with `pip install pibot` or `uv add pibot` and run with `pibot`.

3. **Helm chart → GHCR**
   - Chart lives in `charts/pibot/`; version is aligned with the app (combined versioning).
   - On release, the chart is packaged and pushed to `oci://ghcr.io/<owner>` (chart name/tag inferred by Helm).
   - Install: `helm install pibot oci://ghcr.io/<owner>/pibot --version <version>` (set env from Secret or values).

Do not conflate Docker and PyPI; Helm chart publish runs on the same release and uses the app version from `pyproject.toml`.

Releases are automated with **Release Please**: conventional commits on `main` produce a Release PR (version bump in `pyproject.toml` only; no CHANGELOG.md). Merging that PR creates the tag, GitHub Release (with release notes), and triggers Docker Hub + GHCR (image), PyPI, and Helm chart (GHCR) publish. No direct push to `main` is required.

## Commands

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run bot | `uv run pibot` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Rebuild API docs | `uv run sphinx-apidoc -f -o docs/source src/pibot` |
| Build package (sdist/wheel) | `uv build` |
| Publish to PyPI | `uv publish` |
| Docker build (local) | `docker build -t pibot:local .` |
| Docker run | `docker run --env-file .env pibot:local` |
| Docker publish (multi-arch to Docker Hub / GHCR) | Via release; local: `docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .` |
| Helm install (from GHCR) | `helm install pibot oci://ghcr.io/<owner>/pibot --version <version>` |

## Environment

- Config via `.env`; see `.env.example` for variables.
- Requires a Discord bot token and (for full features) MongoDB and DeepL API key.

## Conventions

- Prefer `uv run` for all Python/tool invocations in this repo.
- For active development, run with `uv run pibot`. Docker and PyPI are the two publish targets (Docker Hub and PyPI), not for day-to-day dev.
- Entry point is `pibot:run` (see `pyproject.toml`).
