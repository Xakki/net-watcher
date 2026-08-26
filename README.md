# Net Watcher

Net Watcher is a non-commercial observational network-research landing draft for **net.xakki.pro**. It collects no visitor input, loads no external assets, and publishes no findings.

## Status

- Draft only; no study or real-data execution is active.
- Work is public/synthetic-only and gated source access is not approved.
- The tracked publication gate remains closed until a provider is approved.
- Deployment, DNS, TLS, hosting, and publication are separate decisions.

## Local use

Requirements: Docker Engine with Compose, GNU Make, Python 3, and curl.

```sh
make help
make config
make test
make kanban-lint
make lint
make verify
make build
```

Production reserves `10210-10219/tcp` and binds web to `172.17.0.1:10210`. The test mirror reserves `11210-11219/tcp` and binds web to `127.0.0.1:11210`. See [docs/ports.md](docs/ports.md).

## Governance and policy

- [Roadmap](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Research policy](docs/research-policy.md)
- [Publication policy](docs/publication.md)
- [Public decisions](docs/decisions.md)
- [Deployment runbook](DEPLOY.md)
- [Publication boundary](publication-boundary.json)
- [Public tasks](.claude/kanban/)

The strongest interpretation is association only: observations cannot establish cause, intent, responsibility, or maliciousness. Methodology separates registration-event, routing-observation, and validation-snapshot time.

`make verify` is local and non-publishing. `make publish-check` additionally requires final tracked publication decisions and currently fails only because `provider` is `null`.

## Corrections and contributions

Use [GitHub Issues](https://github.com/Xakki/net-watcher/issues) for public-safe corrections. Do not include private records, credentials, restricted source material, or review evidence. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
