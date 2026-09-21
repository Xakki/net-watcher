# Phase 2 lesson review kit

This kit prepares for a small Phase 2 educational review of the accepted
Phase 1 synthetic lesson, "Earlier registration change, later route change"
(the case study on the public landing page, section id `synthetic-case`).
Explicit owner approval is a precondition that must exist before any review
round starts; no review is active now. It is a repository reference, not a
served page, and it contains no mechanism to invite reviewers, run a
session, or collect data. Those actions are owner-only and happen
separately, outside this repository.

## Reviewer brief

Use only the public lesson artifact: the "Earlier registration change, later
route change" case study on the landing page (fixture rules, the three
clocks, the tempting conclusion, the evidence audit, the defensible
conclusion, and the self-check). Do not consult any other page, log, dataset,
tool, or live source. The lesson is self-contained; nothing outside it is
needed or permitted for this review.

## Review tasks

Complete the following three tasks, based only on the lesson content:

1. **Identify the tempting inference.** State, in your own words, the
   conclusion the lesson tempts a reader toward, and explain briefly why it
   is tempting given the ordering shown.
2. **Name the missing evidence.** State what would need to be true, or what
   would need to be additionally known, for the tempting inference to be
   supportable, and explain why the lesson does not supply it.
3. **Explain why the conclusion stays observational.** State the conclusion
   the lesson's evidence actually supports, and explain why it stops short of
   causation, intent, ownership, or responsibility.

Written responses only; no session recording, timing, or identifying
information is requested or should be included.

## Scoring rubric

Score each task independently as **met**, **partly met**, or **not met**.
Descriptors below are anchored to the lesson's own content; a reviewer's
wording does not need to match, only the substance.

### First task — identify the tempting inference

- **Met:** Names the inference "the registration change caused the route
  change because it came first," and connects it to the ordering of the
  registration clock (claimed version-processed time) coming before the
  routing clock (observed route time). Naming the validation clock (when
  the two descriptions were checked together) as part of the ordering is
  not required but does not count against the response.
- **Partly met:** Names a causal-sounding conclusion but does not tie it to
  the specific ordering, or conflates the tempting inference with the
  defensible conclusion.
- **Not met:** Cannot state a tempting inference, or states one unrelated to
  ordering or causation.

### Second task — name the missing evidence

- **Met:** Identifies at least one concrete gap, grounded in the lesson's own
  wording, from either of two equivalent lesson lists. From the evidence
  audit: that the registration clock is a claimed/reported time rather than
  an observed event time, that the routing clock reflects one vantage point
  rather than a first-seen time everywhere, that resolution is minute-level
  with unaligned clocks (so overlap and ordering are uncertain), or that
  competing explanations (shared unobserved trigger, independent scheduling,
  processing/propagation delay) are unruled-out. From "what would reduce
  uncertainty": independently documented event semantics, aligned clock
  precision, repeated observations from distinct vantage points, or a
  pre-specified comparison window. A response citing any single item from
  either list, tied to why the tempting inference is unsupported, qualifies
  as met.
- **Partly met:** Gestures at "more data would help" or "more certainty is
  needed" without naming a specific item from either list above.
- **Not met:** States no missing evidence, treats the existing three clocks
  as already sufficient to confirm causation, or recasts a named gap as
  support for a causal, intent, or responsibility reading instead of a limit
  on one.

### Third task — explain why the conclusion stays observational

- **Met:** States that the fixture supports only an association in reported
  order (a version transition reported before a route state was observed),
  and explicitly excludes causation, intent, ownership, responsibility, or
  direction of influence, referencing claimed-vs-observed time, the
  unaligned/minute-level clocks, or the validation clock (the later snapshot
  that only confirms the two descriptions coexisted, not that either caused
  the other) as the reason.
- **Partly met:** Correctly avoids causal language but does not explain why
  (no reference to claimed-vs-observed distinction, vantage-point limits, or
  clock resolution).
- **Not met:** States or implies a causal, intent, or responsibility
  conclusion.

## Consent and no-data statement

- Participation in any Phase 2 review session is explicitly approved by the
  owner in advance and is voluntary for each reviewer.
- No visitor analytics, tracking, or telemetry is collected from the review,
  the landing page, or any reviewer's use of either.
- No accounts, sign-ups, or identifying credentials are required or created.
- No unsolicited outreach is part of this kit; inviting reviewers is a
  separate owner action, done outside this repository.
- No recordings (audio, video, or screen) of any review session are made.
- No names, contact details, affiliations, or raw reviewer responses are
  recorded in this repository. Only the aggregate, non-identifying tallies
  described below belong here.

## Owner decision-record template (blank)

Before any review round, copy this blank template to a private location
outside this repository, and fill it only there, with aggregate,
non-identifying counts. **Never fill in or commit a filled record in this
repository — this file keeps only the blank template.** A filled record is
private review material and must not be committed to this public repository
(see `AGENTS.md`, which prohibits private review material and evidence in
this repository).

```
Review round: [owner-internal reference, not a repository artifact]

First task (identify the tempting inference):  met [k] / partly [k] / not met [k] of [n] reviewers
Second task (name the missing evidence):       met [k] / partly [k] / not met [k] of [n] reviewers
Third task (conclusion stays observational):   met [k] / partly [k] / not met [k] of [n] reviewers

Unattributed confusion points observed (no reviewer identity, no verbatim
quote that could identify a reviewer):
- [ ]
- [ ]

Stop-rule check (from docs/development-strategy.md):
- [ ] Reviewers could distinguish a claimed timestamp from an observation
- [ ] Reviewers did not infer causation from ordering after the worked explanation
- [ ] At least one competing explanation was identified per reviewer
- [ ] Accessibility, synthetic-only, and no-analytics boundaries held throughout

Outcome (choose one): revise / pause / prepare another synthetic case

Rationale: [aggregate, uncertainty-aware summary only; no row-level or
identifying detail]
```

## Out of scope

This kit is a reviewer brief, scoring rubric, consent statement, and blank
decision-record template only. It does not invite or contact reviewers, run
or schedule a review session, or collect, transmit, or store any reviewer
data. Those remain separate, owner-only actions outside this repository.
