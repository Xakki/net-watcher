# Contributing

Contributions that improve clarity, accessibility, methodology, boundary enforcement, or reproducibility are welcome.

## Before opening a change

1. Use the relevant issue template to describe the correction or concern.
2. Do not post private, restricted, person-level, organization-contact, or credential material.
3. Keep the served page English-only, static, and free of scripts, forms, external assets, visitor measurement, and findings.
4. Keep publication decisions in `publication.json`; never render a provider placeholder.

## Local checks

```sh
make config
make test
make lint
make verify
make build
make smoke
make down
```

`make publish-check` is expected to fail while the hosting provider remains unapproved. A change that proposes publication must include a final provider decision and make that gate pass without bypasses.

## Pull requests

Keep changes focused and explain the evidence behind factual or methodological edits. State which commands passed. Do not include generated caches, local environment files, screenshots with machine details, or runtime records.
