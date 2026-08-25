# Reserved port and shared-nginx contract

Net Watcher owns one host listener for upstream use:

| Bind | Container | Purpose |
| --- | --- | --- |
| `127.0.0.1:18137` | `8080/tcp` | Static site and health check |

No metrics, debug, administration, or secondary listener is defined.

## Upstream protocol

- Shared nginx connects with HTTP/1.1.
- TLS terminates at shared nginx.
- `GET /healthz` returns status `200` with the exact body `ok` followed by a newline.
- The application does not use WebSocket or server-sent events.
- The listener remains localhost-only and must not be exposed by a public firewall rule.
- Net Watcher does not own host ports 80 or 443.

The local Compose file is the source of truth for the bind. A port collision must stop startup; choosing another default or binding broadly is not an automatic fallback. A temporary `PORT` Make variable is for isolated local checks only and does not change this reserved upstream contract.

Configuration of shared nginx is an operator action outside this repository. This contract does not authorize DNS, TLS, firewall, or publication changes.
