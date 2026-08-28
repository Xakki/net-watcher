### Complete independent publication review

**Criticality:** Blocking

**TAGS:**
- review
- publication

**Description:**
Obtain independent methodology, privacy, security, accessibility, and publication review of the exact draft.

**Problem:**
Implementation checks cannot substitute for independent review.

**Impact:**
Publication remains ineligible without a documented external verdict.

**Recommendation:**
Define reviewer scope and review the exact candidate after NW-1 and NW-2.

**Acceptance Criteria:**
- NW-1 and NW-2 are complete.
- Required review disciplines and exact artifact are approved.
- Public records contain no reviewer identity or private evidence.

**Decisions:**
- Review evidence remains outside public cards.
- Approved roles are: one methodology and privacy reviewer; one security and publication-boundary reviewer; and one accessibility reviewer, followed by a separate integrator verdict.
- Conflict-of-interest control: each reviewer is independent for its assigned scope, and the integrator is a separate role from the discipline reviewers.

**Execution Log:**
- Started independent publication review.
- The exact review candidate is the tracked publication contract defined by `publication-boundary.json` at the resulting clean branch tree.
- The first exact candidate received three blocking discipline verdicts; fixes reconciled terminology, closed external-asset bypasses, and corrected contrast.

**Review verdict:**
- PASS. The required methodology/privacy, security/publication-boundary, and accessibility approvals cover the exact tracked candidate; the clean worktree was independently confirmed before this transition.
- NW-1 and NW-2 are complete. Publication remains blocked by the unset provider, the publication gate, and separate human authorization.
