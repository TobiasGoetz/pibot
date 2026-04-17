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

Optional: `--set COMMAND_SYNC_BEHAVIOR=global` (default) or `local`, and `--set ENABLE_DEV_TOOLS=false` (default) or `true`.
