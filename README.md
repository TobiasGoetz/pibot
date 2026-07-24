# PiBot

A discord bot providing administration and utility features!

## Features

* Easy to run (uses Python)
* Modular cog-based architecture
* MongoDB integration for per-guild feature settings (sparse storage — only non-default values)
* DeepL translation support
* AI channel summaries (Cloudflare)
* Development tools for testing

## Guild settings

Each feature cog owns its configuration. Administrators use slash commands under `/<feature> settings`:

| Command | Description |
| ------- | ----------- |
| `/<feature> settings view` | List all settings and current values |
| `/<feature> settings set <setting> <value>` | Change one setting |
| `/<feature> settings reset <setting>` | Restore one setting to its default |

Features with settings today:

| Feature | Examples |
| ------- | -------- |
| `general` | `prefix`, `commandChannelId`, `countdownMaxSeconds` |
| `admin` | `maxClearAmount`, `enabled` |
| `summarize` | Limits, model override, `enabled` |
| `translations` | `enabled` |

Cloudflare and DeepL credentials are required at bot level via `PIBOT_*` environment variables (see [Environment variables](#environment-variables)). Per-guild `enabled` flags toggle each feature on a server.

Settings are stored in MongoDB under `features.<featureName>`. Only values that differ from the model defaults are written.

To add settings for a new feature: subclass `SettingsGroup` in `cogs/<feature>/config.py`, mix in `FeatureSettingsMixin` on the cog, and set `settingsGroup = YourConfig`.

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

You can configure the deployment via `pibot:` in the chart [values file](charts/pibot/values.yaml) (and overrides); see [charts/pibot/README.md](charts/pibot/README.md).

Further release and command details: [AGENTS.md](AGENTS.md).

## Environment variables

Configure these for `docker run`, `pibot:` Helm values, or a `.env` file (see `.env.example`). All variables use the ``PIBOT_`` prefix.

**Naming:** ``PIBOT_{NAME}`` for bootstrap/runtime; ``PIBOT_{FEATURE}_{VENDOR}_{FIELD}`` for feature integrations (e.g. ``PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL``).

| Variable        | Required | Default       | Options                                                       | Description                                                                                                                                 |
| --------------- | -------- | ------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `PIBOT_DISCORD_TOKEN` | Required | —             | —                                                             | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications).                                                 |
| `PIBOT_MONGODB_URI`   | Required | —             | Standard MongoDB URI (`mongodb://…`, `mongodb+srv://…`, etc.) | Connection string for your MongoDB instance (local or Atlas).                                                                               |
| `PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL` | Required | — | Cloudflare AI Gateway base URL (through `/compat`) | Bot fails to start if unset. |
| `PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN` | Required | — | — | Cloudflare AI Gateway token. Bot fails to start if unset. |
| `PIBOT_TRANSLATIONS_DEEPL_API_KEY` | Required | — | — | DeepL API key for flag-reaction translations. Bot fails to start if unset. |
| `PIBOT_COMMAND_SYNC_BEHAVIOR` | Optional | `global` | `global`, `local` | Startup slash-command sync. Invalid values fail at startup. Loaded via ``BotConfig`` in ``pibot/config.py``. |
| `PIBOT_ENABLE_DEV_TOOLS` | Optional | `false` | `true`, `false` (also `1` / `0`) | Load the DevTools cog when true. Unset → false. Loaded via ``BotConfig`` in ``pibot/config.py``. |
| `PIBOT_LOG_LEVEL` | Optional | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | Logging level for ``discord.utils.setup_logging``. Unknown values fall back to ``INFO``. |

## Local development

### Prerequisites

* Python 3.14 or higher
* [uv](https://github.com/astral-sh/uv) package manager
* MongoDB instance (local or remote)
* Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)

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

Defaults are **`PIBOT_COMMAND_SYNC_BEHAVIOR=global`** and **`PIBOT_ENABLE_DEV_TOOLS=false`**. For local development without global sync at startup, set **`PIBOT_COMMAND_SYNC_BEHAVIOR=local`**; enable DevTools with **`PIBOT_ENABLE_DEV_TOOLS=true`** and use DevTools `sync` for guild-scoped command testing. See [AGENTS.md](AGENTS.md).

### Linting, types, docs, and releases

See [AGENTS.md](AGENTS.md) for Ruff/`ty` commands, Sphinx doc regeneration, Docker/Helm/PyPI flows, and Release Please.

## Docker (local builds)

To build and run the image on your machine (no registry push):

```bash
docker build -t pibot:local .
docker run --env-file .env pibot:local
```

For day-to-day development, `uv run pibot` is usually faster than rebuilding images.
