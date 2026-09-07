---
name: documentation-roadmap-review
description: Use for independent roadmap/status documentation reviews.
version: 1.0.0
metadata:
  hermes:
    tags: [documentation, roadmap, review, kanban, evidence]
    related_skills: [integrated-diff-review, review-repair-verification]
---

# Documentation and Roadmap Review

Use this for an independent review of roadmap, priority, release-status, or
Kanban documentation changes. The output is an evidence-backed `APPROVE` or an
actionable `REQUEST CHANGES`; do not edit, commit, or push during review.

## Workflow

1. Freeze the review snapshot: record branch, baseline, HEAD, working-tree
   status, changed-file list, diff stat, and `git diff --check`.
2. Review the complete baseline-to-HEAD diff, not only the latest repair commit.
   Inventory every changed factual claim: status, priority, dependency order,
   scope, completion, and dates.
3. Reconcile each claim with the current source of truth. For Kanban-backed
   roadmaps, verify card existence and directory (`todo/`, `grooming/`,
   `ready/`, or `done/`) and inspect the card's dependencies, acceptance
   criteria, and execution evidence. A prior review or execution log is
   supporting evidence, not a substitute for current-tree inspection.
4. Validate dependency chains semantically, not lexically. Confirm that the
   stated order satisfies the referenced cards' explicit dependencies, including
   indirect dependencies and intentionally deferred work.
5. Validate every newly introduced cross-reference. Confirm the target exists,
   has the intended lifecycle state, and is not a stale or renamed identifier.
6. Preserve lifecycle distinctions. `ready for review` or `handoff ready` does
   not mean all future rollout gates are complete. If rollback, reclaim,
   production-scale, or handoff checks remain acceptance requirements, the
   roadmap must say so and must not describe them as completed evidence.
7. Check scope minimality: documentation-only changes should not imply source,
   deployment, secret, or runtime changes. Check that dates and “current order”
   labels are supported by the inspected tree.
8. Repeat the snapshot immediately before the verdict. If the tree moved, redo
   any affected conclusions.

## Findings and verdict

- `HIGH`: a false completion/priority claim could authorize unsafe rollout,
  bypass a dependency, or misrepresent a security or production gate.
- `MEDIUM`: a status/order/link inconsistency can misdirect execution or block
  handoff.
- `LOW`: stale wording or bounded documentation maintenance issue.

For every finding include severity, `path:line`, impact, and a concrete evidence
path. Return `APPROVE` only when no actionable findings remain. State skipped
runtime or external checks explicitly; never convert unavailable verification
into a green claim.

## Common pitfalls

- Reviewing only the repair commit and missing earlier changed claims in the
  branch.
- Treating a card's presence in `ready/` as proof that every acceptance check
  is complete.
- Assuming a numbered API sequence is correct without checking card
  dependencies.
- Accepting a wiki-style reference because its slug looks plausible without
  confirming a matching current card.
- Treating a clean documentation diff as proof that the underlying runtime is
  healthy.

## Related detail

For broader cross-cutting diff review and contract parity checks, also consult
`integrated-diff-review`. For post-repair evidence boundaries, consult
`review-repair-verification`.
