---
name: documentation-source-landscape
description: "Use for documentation-only source discovery before access."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Sources, Documentation, Licensing, Scope]
    category: research
---

# Documentation-Only Source Landscape Discovery

Use this skill when a task asks for a pre-authorization survey of public data
sources, source families, schemas, terms, access policies, or limitations,
while forbidding retrieval or analysis of actual records.

## Operating boundary

1. Treat the task as documentation reconnaissance, not research execution.
2. Read only public documentation, schema/format descriptions, terms,
   licensing, access-policy, and coverage pages.
3. Never inspect records, examples that are actual data, live API responses,
   feeds, archives, samples, downloads, or endpoint results.
4. Do not create credentials, query APIs, stream data, archive source content,
   correlate identifiers, compute findings, or publish outputs.
5. If the selected question or estimand is missing, state that explicitly and
   describe only schema-level fit to the apparent question class.

## Procedure

1. **Frame the decision.** Record source classes A/B, the apparent question,
   and every missing dimension: population, unit, identifier, geography,
   time window, denominator, output, and privacy constraints.
2. **Find named families.** For each class, identify a small set of plausible
   families, preferably first-party documentation. Separate authoritative
   registries from aggregators, archives, tooling, and derived services.
3. **Extract only decision facts.** For every candidate capture: documented
   scope, fields/events/state model, time semantics, coverage, access path,
   terms/licensing, privacy constraints, stability, and known limitations.
4. **Distinguish events from snapshots.** A version history or explicit action
   field may support event-like reconstruction; a daily allocation snapshot is
   not a transaction log. A routing update is an observation, not causal proof.
5. **Assess independence.** Identify whether a candidate is a measurement
   network, a mirror, an aggregation layer, or a parser. Do not count a parser
   over two providers as a third observer.
6. **Ground claims while drafting.** Reset the citation ledger, register each
   documentation URL at retrieval time, cite each externally sourced claim
   inline, render the Sources block mechanically, and run citation verification.
   Keep citations to at most three per sentence; split dense sentences when
   necessary, especially outside markdown tables.
7. **Recommend the smallest next authorization.** Name one candidate per
   class, a fixed scope/time window, permitted fields, protocol, retention,
   review, and publication gates. Phrase this as “consider” or “authorize
   later,” never as approval.
8. **Close with unknowns and non-authorization.** Explicitly list unresolved
   terms, coverage, identity, timing, privacy, and licensing questions. State
   that protocol, output, review, correlation, retrieval, processing,
   retention, and publication remain unauthorized.

## Report shape

- Boundary and question-fit caveat.
- Class A table: family; documented scope/schema fit; terms/access; limits;
  future-access posture.
- Class B table with the same columns.
- Trade-off comparison and decision.
- Minimal next authorization scope.
- Unknowns and explicit non-authorization.
- Mechanically rendered `Sources` list with direct URLs.

## Pitfalls

- Do not infer global completeness from a public registry or collector archive.
- Do not call allocation dates, object versions, or BGP updates causal events
  without an explicit methodological authorization.
- Do not treat an API documentation page as evidence that the API may be
  queried now; documentation review and access approval are separate.
- Do not collapse regional RIR histories into a cross-RIR event stream without
  field-equivalence, identity, clock, and coverage review.
- Do not recommend raw-data caching merely because a tool supports it; raw
  retention requires separate authorization.
- Do not cite search snippets for claims that require page-body details; fetch
  and cite the first-party documentation page instead.

## Supporting detail

For a reusable registration/routing source pattern and documented trade-offs,
see `references/registration-routing-source-patterns.md`.

## Verification checklist

Before delivery, confirm that no records/endpoints were inspected, every named
candidate has scope/terms/limitations notes, unknowns are explicit, future
access is conditional, and the report says protocol/output/review/publication
remain unauthorized. Run the citation ledger verifier; if markdown-table
parsing produces density warnings, reduce citations per sentence rather than
hand-editing the ledger or omitting source URLs.
