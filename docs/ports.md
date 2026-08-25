# Reserved port and shared-nginx contract

Net Watcher owns two ten-port ranges. Only the web ports are currently assigned;
the remaining ports are reserved and have no listeners.

| Environment | Reserved range | Assigned bind | Container | Purpose |
| --- | --- | --- | --- | --- |
| Production | `10210-10219/tcp` | `172.17.0.1:10210` | `8080/tcp` | Static site and health check |
| Test mirror | `11210-11219/tcp` | `127.0.0.1:11210` | `8080/tcp` | Isolated mirror smoke and acceptance checks |

Ports `10211-10219` and `11211-11219` are reserved for Net Watcher but
unassigned. No metrics, debug, administration, or secondary listener is defined.

## Upstream protocol

- Shared nginx connects with HTTP/1.1.
- TLS terminates at shared nginx.
- `GET /healthz` returns status `200` with the exact body `ok` followed by a newline.
- The application does not use WebSocket or server-sent events.
- The production listener is bound only to the host docker bridge so the
  `shared-nginx` container can reach it. The test mirror remains localhost-only.
- Neither range may bind to `0.0.0.0` or be exposed by a public firewall rule.
- Net Watcher does not own host ports 80 or 443.

The Compose file is the source of truth for the production bind. A port collision
must stop startup; choosing another default or binding broadly is not an automatic
fallback. Test mirror commands explicitly use `BIND=127.0.0.1:11210`.

Configuration of shared nginx is an operator action outside this repository. This contract does not authorize DNS, TLS, firewall, or publication changes.
