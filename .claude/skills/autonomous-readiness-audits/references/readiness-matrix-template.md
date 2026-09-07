# Readiness Matrix Template

Use one row per card and keep evidence concise.

| Card | Implementation autonomy | Acceptance side-effect gate | Direct predecessors | Roadmap position | Handoff/push gate | Evidence |
|---|---|---|---|---|---|---|
| `ID` | Yes / conditional / no | None / describe approval | `ID`s or none | canonical sequence | required / not required / governance-only | card lines + source/test lines |

For each row, add:

- **Resolved decisions:** settled policy that must not be reopened.
- **Open questions:** unresolved product/security/engineering choices, if any.
- **Current static evidence:** source, configuration, tests, and generated artifacts.
- **Rerun evidence:** exact read-only commands and honest results.
- **Gap:** missing harness, unavailable runner, unverified rollout, or absent
  acceptance surface.

For an epic, list direct dependency edges separately from the canonical sequence.
Mark logically independent children that are intentionally serialized by roadmap
or governance. Treat production rollout, host-local cleanup, migration, and
external verification as operational gates even when implementation is fully
autonomous.
