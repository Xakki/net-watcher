# Public decisions

## Research posture

Net Watcher is a non-commercial observational project. Current work is limited to public and synthetic material, with no active study or real-data execution.

## Interpretation

Published language may describe association only and must not claim cause, intent, responsibility, or maliciousness. Registration, routing observation, and validation snapshot are distinct clocks.

## Conditional source-selection record

The documentation-only comparison records **RIPE historical objects + RIPE RIS** as a conditional candidate pair for a narrowly scoped, aggregate study. RIPE historical objects provide versioned object history within the RIPE Database, while RIPE RIS provides collector-based routing observations; neither documentation set establishes globally complete coverage or causal linkage.[3][4][11][12][13] This is a documentation-derived candidate decision, not source-access approval.

Any future consideration is disqualified unless all of the following are completed and approved **before any separate future authorization is requested or granted**:

- source terms and privacy review;
- validated event-time semantics, keeping registration-event time, routing-observation time, and validation-snapshot time distinct;
- an approved resource-level linkage rule that excludes personal, contact, and identity data;
- a defined study scope and denominator;
- a fixed RIS collector and peer scope, including the named collectors, peers, and interval, with no scope expansion by convenience;
- a pre-registered routing observation choice of update files versus periodic RIB checkpoints (and the rule for treating the other type as out of scope), rather than a post hoc selection;
- a pre-registered identifier-normalization rule, source/version cutoff, and missingness and exclusion rules, including how withdrawn, unresolved, duplicate, or otherwise unavailable identifiers are handled;
- an approved list of permitted fields for each source and linkage, with raw-data retention prohibited unless expressly listed, derived-data retention bounded, and deletion timing and verification recorded;
- an approved aggregate protocol, pre-registration, suppression controls, and ledger controls;
- a written request-rate and access protocol covering the permitted interface, authentication/account prerequisites, concurrency, backoff, caching, and stop conditions;
- a fixed, pre-declared output location under the tracked public boundary, with no ignored or ad hoc local output, plus an independent human review gate for the exact output artifact; and
- separate explicit authorization for source access, requested only after every condition above is satisfied.

No records, APIs, downloads, processing, correlation, output, or release are authorized by this record. Current work remains public/synthetic-only; any later result would require separate review and authorization under the repository's publication boundary.

Source basis: [`docs/nw6-source-landscape.md`](nw6-source-landscape.md), citations [3], [4], and [11]–[13].

## Publication boundary

The tracked and served sets are exact manifest allowlists. Local ignored namespaces are outside verification input and must never be published. Future findings, if approved, are aggregate and uncertainty-aware.

## Release posture

GitHub Issues is the correction endpoint. The canonical approved provider is `shared nginx at net.xakki.pro`. Exact-artifact independent review and separate authorization for hosting, DNS, TLS, and publication are required.
