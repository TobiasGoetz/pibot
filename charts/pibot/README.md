# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Config vs secrets

- **Credentials** — only via `secretRef.name` (existing Secret, e.g. ExternalSecret). The chart never accepts plaintext tokens for Discord/Mongo/API keys.
- **Non-secrets** — `pibot.logLevel`, `pibot.commandSyncBehavior`, `pibot.enableDevTools` as plain Deployment env.
- **Valkey** — in-cluster subchart by default (generates a password Secret and injects authenticated `PIBOT_VALKEY_URI`). For external Valkey, set `valkey.enabled=false` and put `PIBOT_VALKEY_URI` in the Secret.

## Valkey subchart

PiBot caches guild settings in Valkey. The chart includes the upstream [valkey-helm](https://github.com/valkey-io/valkey-helm) chart and enables it by default:

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd
```

Omit `PIBOT_VALKEY_URI` from the Secret. The chart creates `<release>-valkey-users` (random password, stable across upgrades via lookup), enables Valkey ACL auth for the `default` user, and injects `PIBOT_VALKEY_URI` from that Secret. Defaults: auth on, 1Gi data PVC. Override under `valkey:` in [values.yaml](values.yaml); see the upstream chart for full options.

To use external Valkey: `--set valkey.enabled=false` and provide `PIBOT_VALKEY_URI` in the Secret. To keep the subchart but disable auth: `valkey.auth.enabled=false` (plain `valkey://<release>-valkey:6379/0` is injected instead).

## Install from GHCR

```bash
# Secret must already exist with keys such as:
#   PIBOT_DISCORD_TOKEN, PIBOT_MONGODB_URI,
#   PIBOT_TRANSLATIONS_DEEPL_API_KEY,
#   PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL, PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN
# Plus PIBOT_VALKEY_URI only when valkey.enabled=false

helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd
```

See [values.yaml](values.yaml) for all options.
