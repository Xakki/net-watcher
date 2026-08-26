# Architecture

Net Watcher is a static HTML and CSS landing served by an unprivileged container. The image contains only the exact served allowlist. Compose binds the production reservation to the host bridge and the test mirror to loopback; the container listens on port 8080.

## Trust boundaries

The public repository contains policy, synthetic/public fixtures, build configuration, and the static landing only. It has no application API, database, queue, cache, analytics, account system, collection pipeline, or outbound data path.

No customer, request, analytics, credential, storage, deployment, or research-derived data may cross into this research lane. Current source access is not approved and real-data execution is unavailable.

## Verification

`publication-boundary.json` names every tracked public file and served file. Local verification opens every worktree component descriptor-relatively without following links, uses bounded regular-file reads, scans the full publication set, and fails on unexpected files or disclosure classes. Publication verification additionally requires a clean index and worktree, then validates paths, regular-file modes, and bytes from the immutable committed `HEAD` tree. The Kanban verifier independently validates the public board.

The semantic scanner treats each normalized decoded file view independently. CRLF and lone CR are canonicalized to LF before segmentation; U+2029 is a paragraph boundary, and U+2028 is a line/sentence boundary. Blank lines delimit paragraphs; terminal punctuation, semicolons, and line breaks delimit sentence units inside a paragraph. Registry onboarding signals must occur in one sentence. A registry resource workflow must occur in one sentence or in two adjacent sentence units in the same paragraph, with one unit naming the registry and the other naming the operation. Matches never join paragraphs or files, and no character-distance window substitutes for these structural boundaries.

Build, local rehearsal, publication eligibility, and external release are separate states. None authorizes the next.

Claude Code permission denies are defense in depth for cooperative tool use, not an operating-system sandbox. Ignored private and local paths remain outside the publication boundary even when an arbitrary subprocess could bypass a tool-level rule.
