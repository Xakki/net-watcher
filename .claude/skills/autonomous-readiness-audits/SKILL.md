---
name: autonomous-readiness-audits
description: Use for autonomous task-pool and dependency audits.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [readiness, autonomy, dependencies, acceptance, roadmap, governance]
---

# Autonomous Readiness Audits

## When to Use

Use when reviewing a proposed pool of repository tasks before user approval,
especially when cards span code, tests, docs, infrastructure, deployment, or
multiple epics. Produce a read-only readiness verdict; do not edit, commit,
push, deploy, or silently resolve product/security choices.

## Workflow

1. Freeze the repository snapshot: path, branch, `HEAD`, worktree status, and
   relevant card locations. Preserve unrelated worktree state.
2. Read each complete card, including Description, Acceptance Criteria,
   Decisions, predecessors, subtasks, integration checklist, and Open questions.
   Verify cross-references in the roadmap and neighboring epic cards.
3. Give every card three independent verdicts:
   - **Implementation autonomy:** can the code/docs/tests be completed from the
     resolved scope without a user product or security decision?
   - **Acceptance autonomy:** do rollout, deletion, production verification,
     migration, or other side effects require explicit operational approval?
   - **Ordering/handoff gate:** does a technical predecessor or governance rule
     require completion and handoff before the next card? Keep technical
     dependency distinct from policy-driven serial roadmap order.
4. Trace the current implementation and tests. Confirm whether the acceptance
   surface exists, is partially implemented, or is absent. Passing internal
   tests does not prove frontend, HTTP, deployment, generated-artifact, or
   runtime acceptance.
5. Identify tooling gaps without inflating them into product/security gates. For
   example, a card requiring frontend tests in a repository with no frontend
   test harness needs an engineering test strategy, not necessarily user input.
6. Build dependency matrices from direct edges stated in each child card's
   Decisions. Then state the canonical roadmap sequence separately: a child can
   be logically independent yet intentionally serialized.
7. Explicitly identify side-effect gates. A task may be autonomously
   implementable while its acceptance still needs authorization for a remote
   rollout, host-local workaround deletion, production migration, or external
   verification.
8. Run only safe, bounded, read-only verification appropriate to the request.
   Record exact commands and honest outcomes. If a required runner is absent,
   report the setup blocker; never fabricate green results.
9. Return a compact matrix with card, autonomy verdict, gate, predecessor, and
   whether handoff/push is required before the next task. Include evidence file
   and line ranges where practical.

## Decision Rules

- Resolved Decisions are settled policy, not unresolved questions.
- An empty Open questions section does not waive an operational approval needed
  by Acceptance Criteria.
- A roadmap arrow can impose serial execution even when cards have no code
  dependency.
- “Implemented” and “accepted” are separate claims; production evidence must
  be labeled as rerun/current rather than inferred from static code.
- A card with no current test harness may still be autonomous if the test
  mechanism is an ordinary engineering choice; escalate only ambiguous test
  semantics or product/security policy.

## Pitfalls

- Do not equate a clean worktree or passing package tests with task-pool
  readiness.
- Do not treat push/merge as technically required unless the repository's
  governance or handoff model requires it; state the source of the gate.
- Do not authorize production rollout merely because implementation decisions
  are resolved.
- Do not turn an unavailable local binary into a durable claim that the task is
  impossible; report it as an environment blocker and preserve other evidence.

## References

- `references/readiness-matrix-template.md` — compact reporting template for
  autonomy, acceptance, ordering, and dependency evidence.
