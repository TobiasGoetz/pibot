---
name: commit
description: Generates commit messages and PR titles using Conventional Commits for Release Please. Use when writing commit messages, squashing commits, or naming PRs so releases and version bumps are correct.
---
# Conventional Commits (Release Please)

Releases are driven by **Release Please**: conventional commits on `main` produce a Release PR. Use this format so versions and release notes are correct.

## Format

```
<type>(<scope>): <short description>

[optional body]
```

- **type**: `feat` (minor), `fix` (patch), `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- **scope**: optional, e.g. `auth`, `cogs`, `docker`
- **description**: imperative, lowercase after colon, no period at end

## Examples

```
feat(translations): add DeepL language detection
fix(admin): correct permission check for kick command
chore(deps): bump discord-py to 2.7.1
docs: update AGENTS.md with Helm install command
```

## Rules

- Use **imperative** in description: "add feature" not "added feature".
- **feat** and **fix** drive version bumps; other types don't (but still use conventional format).
- No manual CHANGELOG or version edits—Release Please updates `pyproject.toml` and `charts/pibot/Chart.yaml`.
