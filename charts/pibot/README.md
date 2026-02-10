# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Install from GHCR

Pass secrets as arguments at install:

```bash
helm install pibot oci://ghcr.io/TobiasGoetz/pibot --version <version> \
  --set discord.token="..." \
  --set mongodb.uri="mongodb://..." \
  --set deepl.apiKey="..."
```

Optional: `--set environment=production` or `environment=testing`. Image: `--set image.repository=` / `image.tag=` (default `tobiasgoetz/pibot`).
