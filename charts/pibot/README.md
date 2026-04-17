# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Install from GHCR

Pass secrets as arguments at install:

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/pibot --version <version> \
  --set discord.token="..." \
  --set mongodb.uri="mongodb://..." \
  --set deepl.apiKey="..."
```

### Optional tuning

| Values path | Default | Env var |
|-------------|---------|---------|
| `logging.level` | `INFO` | `LOG_LEVEL` |
| `bot.settings.commandSyncBehavior` | `global` | `COMMAND_SYNC_BEHAVIOR` |
| `bot.settings.enableDevTools` | `false` | `ENABLE_DEV_TOOLS` |

`logging` and `bot` are top-level keys; runtime tuning lives under `bot.settings`.

Example:

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set discord.token="..." --set mongodb.uri="..." --set deepl.apiKey="..." \
  --set logging.level=DEBUG \
  --set bot.settings.commandSyncBehavior=global \
  --set bot.settings.enableDevTools=false
```
