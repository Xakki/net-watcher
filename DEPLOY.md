# Deployment contract

No deployment is authorized by this repository state. The planned hostname is `net.xakki.pro`, but DNS, TLS, hosting, and publication remain separate decisions.

## Local rehearsal

```sh
make verify
make build
make up
make smoke
make down
```

This binds the service only to `172.17.0.1:10210` by default so the containerized
shared nginx can reach it without public exposure. Production owns `10210-10219`;
the test mirror owns `11210-11219` and uses `127.0.0.1:11210` for web. See
[docs/ports.md](docs/ports.md) for the complete HTTP/1.1 boundary. The Compose
bridge disables IP masquerading, so the site requires no outbound network access.

## Publication gate

Before any future publication:

1. Approve and record the exact hosting provider in `publication.json`.
2. Keep the correction endpoint exact and reachable.
3. Review all repository changes and run `make verify`.
4. Run `make publish-check`; it must exit successfully without overrides.
5. Independently approve hosting, DNS, and TLS actions.
6. Recheck response headers, page bytes, and the correction link at the final origin.

The Makefile has no deploy or publish target. A successful local check never implies deployment approval. Do not add credentials to this repository or pass them through command arguments.
