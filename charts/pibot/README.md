# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Config vs secrets

- **Credentials** — only via `secretRef.name` (existing Secret, e.g. ExternalSecret). The chart never accepts plaintext tokens.
- **Non-secrets** — `environment`, `logging`, `bot.settings` as plain Deployment env.

## Install from GHCR

```bash
# Secret must already exist with keys such as:
#   DISCORD_TOKEN, MONGODB_URI, DEEPL_API_KEY
# (+ Cloudflare AI tokens if the image needs them)

helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd-pibot \
  --set environment=production
```

See [values.yaml](values.yaml) for all options.
