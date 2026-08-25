# Net Watcher

Net Watcher is a container-first, static research landing draft for the planned host **net.xakki.pro**. It explains a proposed observational network-measurement frame without collecting visitor input, loading external assets, or publishing findings.

## Status

- Draft only; no study is active.
- No results or real research records are included.
- The page uses English, semantic HTML, local CSS, and no JavaScript.
- Deployment, DNS, and TLS changes are out of scope.
- The tracked publication gate remains closed until a hosting provider is explicitly approved.

## Local use

Requirements: Docker Engine with Compose, GNU Make, Python 3, and curl.

```sh
make help
make config
make build
make test
make lint
make verify
make up
make smoke
make ps
make down
```

The default service URL is `http://127.0.0.1:18137`. This is the single reserved localhost upstream; see [docs/ports.md](docs/ports.md) for the HTTP/1.1 shared-nginx contract. To use another free local port for an isolated check without creating a file:

```sh
make up PORT=18138
make smoke PORT=18138
make down PORT=18138
```

All Compose commands are pinned to the `net-watcher` project. `make verify` is local and non-publishing. `make publish-check` validates the same boundary and then fails closed unless both tracked publication decisions are final.

## Public boundary

The served tree contains only `site/index.html` and `site/styles.css`. The verifier rejects unexpected files, scripts, forms, active media, external assets, event handlers, results-like presentation, sensitive record classes, lifecycle identifiers, machine paths, credential-shaped values, oversized files, invalid UTF-8, and disallowed Unicode controls.

The Docker image uses a digest-pinned unprivileged NGINX base. Compose binds only to localhost, uses a non-masquerading isolated bridge, drops capabilities, applies resource limits, mounts writable runtime paths as bounded temporary filesystems, and checks `/healthz`.

## Corrections and contributions

Open a [GitHub issue](https://github.com/Xakki/net-watcher/issues) using the correction, methodology, or privacy/disclosure template. Do not include private records, credentials, or restricted source material in an issue. See [CONTRIBUTING.md](CONTRIBUTING.md) for the review process and [SECURITY.md](SECURITY.md) for responsible disclosure guidance.

## Publication decisions

`publication.json` is the tracked decision record. The correction endpoint is final. The provider remains `null` because no hosting provider has been approved; the provider is deliberately not rendered on the draft page. Do not replace it with a placeholder. `make publish-check` will report the missing provider until an exact, reviewed value is committed.

## License

[MIT](LICENSE)
