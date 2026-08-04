# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Config vs secrets

- **Credentials** — only via `secretRef.name` (existing Secret, e.g. ExternalSecret). The chart never accepts plaintext tokens.
- **Non-secrets** — `pibot.logLevel`, `pibot.commandSyncBehavior`, `pibot.enableDevTools` as plain Deployment env.

## Install from GHCR

```bash
# Secret must already exist with keys such as:
#   PIBOT_DISCORD_TOKEN, PIBOT_MONGODB_URI, PIBOT_TRANSLATIONS_DEEPL_API_KEY,
#   PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL, PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN

helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd
```

See [values.yaml](values.yaml) for all options.
