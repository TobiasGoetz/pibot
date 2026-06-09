# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Install from GHCR

Pass required secrets at install (`discord.token`, `mongodb.uri`). See [values.yaml](values.yaml) for all configurable values.

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set discord.token="..." \
  --set mongodb.uri="mongodb://..."
```
