# PiBot

A discord bot providing administration and utility features!

## Features

* Easy to run (uses Python)
* Modular cog-based architecture
* MongoDB integration for guild settings
* DeepL translation support
* Development tools for testing

## Installation

How to run a **released** build depends on where you want it to run.

### As a Python package

Install from PyPI and run the `pibot` console script:

```bash
pip install pibot
# or: uv add pibot
pibot
```

### As a container image

Each release publishes the **same** image to Docker Hub and to GitHub Container Registry ([workflow](.github/workflows/docker-publish.yml)).

| Registry   | Image reference (example)                                                                                                                                              |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Docker Hub | [`tobiasgoetz/pibot`](https://hub.docker.com/r/tobiasgoetz/pibot): `docker run --env-file .env tobiasgoetz/pibot:latest`                                               |
| GHCR       | `ghcr.io/tobiasgoetz/pibot:latest` (and version tags; path uses a lowercased GitHub `owner/repo`) — e.g. `docker run --env-file .env ghcr.io/tobiasgoetz/pibot:latest` |

To build an image from this repository locally, see [Docker](#docker-local-builds) below.

### On Kubernetes

Install the published Helm chart from GHCR OCI ([workflow](.github/workflows/helm-publish.yml)). Use an app version that matches `pyproject.toml` / the GitHub release:

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version>
```

Configure Discord, MongoDB, DeepL, and other settings via chart values or Secrets.

Further release and command details: [AGENTS.md](AGENTS.md).

## Environment variables

Configure these for `docker run`, Helm values, or a `.env` file (see `.env.example`). Names match what the process reads via the environment.

| Variable        | Required | Default       | Options                                                       | Description                                                                                                                                 |
| --------------- | -------- | ------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `DISCORD_TOKEN` | Required | —             | —                                                             | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications).                                                 |
| `MONGODB_URI`   | Required | —             | Standard MongoDB URI (`mongodb://…`, `mongodb+srv://…`, etc.) | Connection string for your MongoDB instance (local or Atlas).                                                                               |
| `DEEPL_API_KEY` | Required | —             | —                                                             | [DeepL](https://www.deepl.com/pro-api) API key; required because the translation cog loads at startup.                                      |
| `ENVIRONMENT`   | Optional | `development` | `development`, `production`, `testing` | `development` (or omit): DevTools cog, local command sync. `production` or `testing`: global command sync, no DevTools. |

## Local development

### Prerequisites

* Python 3.14 or higher
* [uv](https://github.com/astral-sh/uv) package manager
* MongoDB instance (local or remote)
* Discord bot token from [Discord Developer Portal](https://discord.com/developers/app\lications)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/TobiasGoetz/pibot.git
   cd pibot
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**

   Copy the example environment file and create your `.env` file with your values:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your actual values. See [Environment variables](#environment-variables) for the full list.

4. **Run the bot**
   ```bash
   uv run pibot
   ```

### Behaviour in development

When `ENVIRONMENT` is not set to `production` or `testing`, the **DevTools** cog loads, commands sync locally (not globally), and extra debugging aids are available. For where that is wired in code, see [AGENTS.md](AGENTS.md).

### Linting, types, docs, and releases

See [AGENTS.md](AGENTS.md) for Ruff/`ty` commands, Sphinx doc regeneration, Docker/Helm/PyPI flows, and Release Please.

## Docker (local builds)

To build and run the image on your machine (no registry push):

```bash
docker build -t pibot:local .
docker run --env-file .env pibot:local
```

For day-to-day development, `uv run pibot` is usually faster than rebuilding images.
