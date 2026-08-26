# Contributing

Contributions improving clarity, accessibility, methodology, boundary enforcement, or reproducibility are welcome.

## Public tasks

The directory under `.claude/kanban/` is canonical state. Use only project-local `NW-*` identifiers and reference GitHub Issues when public discussion is useful. Never put histories, machine paths, commit identifiers, reviewer identities, correspondence, private evidence, or restricted records in cards or issues.

## Requirements

- Keep the served page English-only, static, and free of scripts, forms, external assets, visitor measurement, and findings.
- Keep publication decisions in `publication.json`; never use a provider placeholder.
- Update `publication-boundary.json` exactly when tracked public files change.
- Add regression tests before changing verifier behavior.

## Local checks

```sh
make config
make test
make kanban-lint
make lint
make verify
make build
```

`make publish-check` is expected to fail while the provider is unapproved. Pull requests should remain focused and report commands, not raw execution logs or private evidence.
