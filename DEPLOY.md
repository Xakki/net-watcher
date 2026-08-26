# Deployment contract

No deployment is authorized by this repository state. Local rehearsal, publication eligibility, and external release are separate states.

## Local rehearsal

```sh
make verify
make build
make up
make smoke
make down
```

The default binds only to `172.17.0.1:10210`. The isolated test mirror uses `127.0.0.1:11210`. See [docs/ports.md](docs/ports.md).

## Publication eligibility

1. Complete exact-artifact independent review.
2. Approve and record the exact provider in `publication.json`.
3. Keep the correction endpoint exact and reachable.
4. Run `make verify` and `make publish-check` without overrides.
5. Approve hosting, DNS, TLS, and publication as separate human actions.
6. Recheck final-origin bytes, headers, and the correction link.

The Makefile has no deploy or publish mutation target. Never add credentials, provider procedures, host inventory, or private approval evidence to this repository.
