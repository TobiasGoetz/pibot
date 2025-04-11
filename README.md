# PiBot

A discord bot providing administration and music features!

## Features

* Easy to run (uses Python)

## Installation

Coming soon

### Environment Variables

* `DISCORD_TOKEN` - The token for the discord bot
* `MONGODB_URI` - The URI for the MongoDB database

# Local Development

## Documentation

Update docs using `uv run sphinx-apidoc -f -o docs/source src/pibot`

## Building multi-architecture docker images
1. `docker buildx create --use --name pibot`
2. `docker buildx build --platform linux/amd64,linux/arm64 --push -t tobiasgoetz/pibot .`