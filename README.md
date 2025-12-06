# PiBot

A discord bot providing administration and music features!

## Features

* Easy to run (uses Python)
* Modular cog-based architecture
* MongoDB integration for guild settings
* DeepL translation support
* Development tools for testing

## Installation

Coming soon

# Local Development

## Prerequisites

* Python 3.13 or higher
* [uv](https://github.com/astral-sh/uv) package manager
* MongoDB instance (local or remote)
* Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)

## Setup

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
   
   Edit `.env` with your actual values. The `.env.example` file contains all required and optional environment variables with descriptions.

4. **Run the bot**
   ```bash
   uv run python -m pibot
   ```

## Development Workflow

### Running the Bot

The recommended way to run the bot during development is using `uv` directly:

```bash
uv run python -m pibot
```

This provides:
* Fast iteration (no Docker rebuilds needed)
* Easy debugging with IDE integration
* Direct access to logs and file system

### Project Structure

```
src/pibot/
├── __main__.py      # Entry point
├── bot.py           # Main Bot class with cog loading
├── database.py      # MongoDB wrapper
└── cogs/            # Modular command groups
    ├── admin.py
    ├── general.py
    ├── translations.py
    └── devTools.py  # Only loads in development mode
```

### Development Features

When `ENVIRONMENT` is not set to `production` or `testing`:
* **DevTools cog** is automatically loaded with development commands
* Commands sync locally (not globally) for faster testing
* Additional debugging features are available

### Code Quality

The project uses `ruff` for linting and formatting. Run it with:

```bash
uv run ruff check .
uv run ruff format .
```

## Documentation

Update docs using:
```bash
uv run sphinx-apidoc -f -o docs/source src/pibot
```

## Docker

### Testing Docker Build Locally

To test the Docker build locally without publishing:

```bash
docker build -t pibot:local .
docker run --env-file .env pibot:local
```

### Building and Publishing Multi-Architecture Images

**⚠️ This will publish to Docker Hub.** Make sure you're logged in with `docker login` before running.

To build and publish multi-architecture images from your local machine:

1. Create buildx builder (one-time setup):
   ```bash
   docker buildx create --use --name pibot
   ```

2. Build and push multi-arch image to Docker Hub:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .
   ```
   
   This command will build the image for both AMD64 and ARM64 architectures and **push it to Docker Hub**.

**Note:** For active development, using `uv` directly is recommended over Docker for faster iteration.