# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Install from GHCR

Pass required secrets at install (`pibot.discordToken`, `pibot.mongodbUri`). See [values.yaml](values.yaml) for all configurable values.

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set pibot.discordToken="..." \
  --set pibot.mongodbUri="mongodb://..."
```
