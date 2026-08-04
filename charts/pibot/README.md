# PiBot Helm Chart

Deploys [PiBot](https://github.com/TobiasGoetz/pibot) (Discord bot) on Kubernetes.

## Config vs secrets

- **Credentials** — only via `secretRef.name` (existing Secret, e.g. ExternalSecret). The chart never accepts plaintext tokens for Discord/Mongo/API keys.
- **Non-secrets** — `pibot.logLevel`, `pibot.commandSyncBehavior`, `pibot.enableDevTools` as plain Deployment env.
- **Valkey** — either an external URI in the Secret (`PIBOT_VALKEY_URI`), or the optional Valkey subchart (`valkey.enabled=true`), which generates a password Secret and injects an authenticated `PIBOT_VALKEY_URI` on the Deployment.

## Optional Valkey subchart

PiBot caches guild settings in Valkey. Enable in-cluster Valkey via the upstream [valkey-helm](https://github.com/valkey-io/valkey-helm) chart:

```bash
helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd \
  --set valkey.enabled=true
```

When `valkey.enabled` is true, omit `PIBOT_VALKEY_URI` from the Secret. The chart creates `<release>-valkey-users` (random password, stable across upgrades via lookup), enables Valkey ACL auth for the `default` user, and injects `PIBOT_VALKEY_URI` from that Secret. Defaults: auth on, 1Gi data PVC. Override under `valkey:` in [values.yaml](values.yaml); see the upstream chart for full options.

To run without auth, set `valkey.auth.enabled=false` (plain `valkey://<release>-valkey:6379/0` is injected instead).

## Install from GHCR

```bash
# Secret must already exist with keys such as:
#   PIBOT_DISCORD_TOKEN, PIBOT_MONGODB_URI,
#   PIBOT_TRANSLATIONS_DEEPL_API_KEY,
#   PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL, PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN
# Plus PIBOT_VALKEY_URI unless valkey.enabled=true

helm install pibot oci://ghcr.io/tobiasgoetz/helm-charts/pibot --version <version> \
  --set secretRef.name=pibot-prd
```

See [values.yaml](values.yaml) for all options.
