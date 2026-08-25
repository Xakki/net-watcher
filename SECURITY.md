# Security policy

## Supported surface

This repository is a static research landing page and its local container harness. It has no application API, account system, form handling, client-side script, or active research pipeline.

## Report a vulnerability or privacy concern

Use the [privacy and disclosure issue template](https://github.com/Xakki/net-watcher/issues/new?template=privacy-disclosure.yml) when public discussion is safe. If a report would expose a vulnerability, private record, credential, or restricted source, do not place that material in a public issue. Use GitHub's private vulnerability reporting feature when it is enabled for the repository.

Include only the minimum reproducible description. Remove addresses, identifiers, tokens, and third-party records.

## Corrections

Factual, methodological, and attribution corrections belong in the [public issue queue](https://github.com/Xakki/net-watcher/issues). Accepted corrections should update the canonical source, include a regression test when verifier behavior changes, and pass `make verify` and `make publish-check` before any future publication.

## Boundary

- No secrets or credentials belong in Git, issue text, screenshots, build arguments, or logs.
- No real, restricted, person-level, or organization-contact records belong in fixtures.
- No external assets, tracking code, forms, or scripts belong in the served tree.
- Security checks do not authorize deployment or collection.
