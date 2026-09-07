# Open-inventory decision briefs

Use this matrix when a roadmap/Kanban card is blocked on an exact supported-output
or route inventory.

## Evidence matrix

| Question | Evidence to capture |
|---|---|
| What is live now? | Current generated/manual catalog, count, grouped source/target pairs |
| What is only planned? | Card status, profile-only assignments, unpublished discriminators |
| How does it execute? | `executionKind`, stream, worker, output category |
| What security applies? | Sandbox, egress/proxy, URL policy, resource/job limits |
| What is the semantic contract? | Normalized options, defaults/caps, output-object assertions |
| What remains undefined? | Missing dimensions, limits, persistence, or owner decision |

## Option template

For each option, state:

- **Scope:** exact pair/input/output inventory; explicit exclusions.
- **Why coherent:** which existing cards/contracts it aligns with.
- **Risks:** unresolved contract or dependency risks.
- **Acceptance implications:** routing, security, semantic, and end-to-end checks.

Prefer 3–4 options. The recommended option should be the smallest complete scope
whose semantics are already specified. Do not infer a new output contract from
adjacent limits: for example, duration/FPS/file-size limits do not establish
video resize semantics.

## Browser-specific guardrails

A shared resize or rendering semantic does not merge browser execution with image
or video execution. Every browser option must retain its own `executionKind`,
stream, sandbox, egress policy, quota/retention category, and lifecycle limits.
Separate local/self-contained inputs from URL inputs; URL inputs require the
policy-enforcing egress path and per-hop SSRF protections. Distinguish a
profile/catalog assignment from a published live request path: if the request,
entity, retry path, or capability generator cannot carry the discriminator, the
feature is not live.

Historical traces and source inspection are supporting evidence only. Acceptance
of dimensions or output behavior requires a bounded end-to-end job and inspection
of the downloaded result object (for example, actual image/video dimensions),
not merely an accepted API response or normalized options payload.
