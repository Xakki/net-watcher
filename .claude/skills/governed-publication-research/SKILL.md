---
name: governed-publication-research
description: Use for staged approval of public research publication.
---

# Governed publication research

Use for public-research projects where an artifact can be technically live while
publication, data access, output generation, and release remain separately
human-authorized.

## Core principle

Treat every gate as an independent decision. Never infer authorization from a
working service, a green build, a completed review, or a previous adjacent
approval.

## Approval ladder

1. **Question** — approve one narrow, observational research question.
2. **Source class** — authorize a named source class at an explicit access
   level. Documentation discovery is not record access.
3. **Protocol** — approve inclusion/exclusion, temporal semantics, retention,
   uncertainty, and stop rules before collecting or correlating anything.
4. **Aggregate-output contract** — approve suppression, generalization,
   differencing controls, and prohibited claims before generation.
5. **Independent review** — review the exact candidate, separately by relevant
   disciplines, then obtain an integrator verdict.
6. **Publication/release** — separately authorize the exact artifact and any
   external hosting, DNS, TLS, or release action.

Do not collapse these steps. A later approval never retroactively broadens an
earlier one.

## Scope discipline

- Restate permitted actions and prohibited actions in every delegated task.
- For documentation-only research, allow only public documentation, schemas,
  terms, and licensing pages. Explicitly prohibit APIs, records, samples,
  feeds, downloads, archives, queries, correlation, storage, and accounts.
- The output medium is part of scope. If authorization says "returned brief",
  do not create a repository file, plan artifact, card, or public document.
- If work produces an out-of-scope artifact, stop. Ask whether to remove it or
  explicitly retain it; do not commit it by default.
- Review scope drift separately from content correctness. Report severity,
  evidence, repair complexity, and the smallest decision needed.

## Aggregate-only safeguards

Require, before future data access:

- no subject-, event-, address-, route-, organization-, or raw-timestamp-level
  release;
- no causal, intent, ownership, responsibility, maliciousness, or attribution
  claims from observational evidence;
- pre-specified minimum cell sizes, suppression/generalization, complementary
  suppression, and differencing/reconstruction controls;
- uncertainty and limitations in every permitted aggregate result;
- explicit stop conditions for ambiguous authorization, unsafe output,
  unbounded disclosure risk, or review defects.

## Operational release checks

For a static public artifact, distinguish:

- **runtime availability:** edge, upstream, health, byte match, and headers;
- **publication eligibility:** clean repository, exact artifact contract, and
  green sanctioned gates;
- **publication authorization:** human decision for the exact release.

When a TLS edge accepts connections but HTTP stalls, diagnose the upstream
listener before changing DNS or TLS. Confirm the service bind/health contract,
restore only the authorized service, then repeat public IPv4/IPv6 verification.
Do not change proxy, DNS, TLS, firewall, or provider without separate approval.

## Review and commit

- Run independent read-only review after implementation or a state transition.
- A reviewer must check public records for stale statements that contradict new
  provider/release/approval state, not just the changed card.
- Repair direct defects with the smallest scope, rerun sanctioned gates, and
  re-review if the repair changes published records.
- Commit only after explicit approval. Use explicit path staging; preserve
  unrelated work; run the clean-tree publication gate after commit.

## Verification checklist

Before stating a release is complete, confirm:

- exact candidate passes sanctioned verify and publication gates;
- public origin is repeatably reachable on required address families;
- permitted files match expected bytes and headers;
- correction endpoint is reachable where required;
- public records, card state, and validator/manifest state agree;
- repository is clean after the authorized commit;
- no unapproved infrastructure or source/data action occurred.
