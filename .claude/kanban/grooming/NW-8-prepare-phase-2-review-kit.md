### Prepare a bounded Phase 2 educational review kit

**Criticality:** Medium

**TAGS:**
- review
- education
- publication

**Description:**
Prepare a public, synthetic-only review kit for a small, explicitly approved Phase 2 review of the accepted lesson, covering only the parts an agent can deliver in-repo.

**Problem:**
Phase 2 requires reviewers to complete defined tasks against the lesson, but no reviewer brief, scoring rubric, consent statement, or owner decision-record template exists yet.

**Impact:**
Without a prepared kit, any review session would rely on ad hoc materials, risking inconsistent scoring and an unclear consent or data boundary.

**Recommendation:**
Deliver an in-repo review kit. Explicitly exclude inviting or contacting reviewers, running sessions, or collecting any data; those remain separate actions for the owner.

**Acceptance Criteria:**
- A reviewer brief exists that uses only the public lesson artifact.
- The brief states the three Phase 2 tasks: identify the tempting inference, name the missing evidence, and explain why the conclusion remains observational.
- A scoring rubric exists for the three tasks.
- A consent / no-data statement exists: no visitor analytics, no personal research data recorded, no unsolicited outreach, no accounts.
- An owner decision-record template exists covering revise / pause / prepare another synthetic case.
- The kit contains no invitation, contact, session-running, or data-collection mechanism.

**Open questions:**
- Where should the kit live: `docs/` or the served site? Default recommendation is `docs/`, not served.
- Should the kit be served publicly at all, or stay a repository-only reference the owner hands to reviewers directly?

**Decisions:**
- Inviting or contacting reviewers, running review sessions, and collecting any data are explicitly out of scope for agent work; the owner performs those separately.
