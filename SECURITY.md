# Security policy

## Supported surface

This repository is a static research landing and local container harness. It has no application API, accounts, forms, client script, active collection, or research pipeline.

## Reporting

Use the [privacy and disclosure issue template](https://github.com/Xakki/net-watcher/issues/new?template=privacy-disclosure.yml) only when public discussion is safe. For sensitive vulnerabilities or private records, use GitHub private vulnerability reporting when available and provide only a minimized reproduction.

## Boundary

- No secrets, credentials, machine paths, host inventory, provider procedures, or private review evidence belong in Git, issues, screenshots, arguments, or logs.
- No real, restricted, raw, row-level, searchable, minimized-event, audit, person, or organization-contact records belong in the repository.
- No external assets, tracking, forms, scripts, or research-derived product flow are permitted.
- Public reproducibility is limited to public/synthetic code, configuration, manifests, fixtures, and aggregate build instructions.
- Security checks do not authorize collection, deployment, DNS/TLS changes, or publication.

Accepted corrections update canonical sources, add verifier regression coverage when behavior changes, and pass `make verify`.
