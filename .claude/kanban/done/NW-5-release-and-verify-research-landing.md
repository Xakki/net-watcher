### Release and verify the research landing

**Criticality:** Blocking

**TAGS:**
- release
- publication

**Description:**
Perform an authorized release rehearsal and final-origin verification.

**Problem:**
A green local build does not authorize public release.

**Impact:**
Premature release could bypass review and provider decisions.

**Recommendation:**
Proceed only after NW-3, NW-4, final eligibility, and separate human authorization.

**Acceptance Criteria:**
- NW-3 and NW-4 are complete.
- The exact publication gate passes without overrides.
- DNS, TLS, hosting, and publication actions have separate authorization.
- Final-origin bytes, headers, and correction link are verified.

**Decisions:**
- Local rehearsal is not release approval.

**Completion:**
- NW-3 and NW-4 are complete.
- The exact publication gate passes without overrides.
- Separate authorization covers hosting, DNS, TLS, and publication for the exact candidate.
- Final-origin artifact bytes, health, required security headers, and the GitHub Issues correction endpoint are verified over IPv4 and IPv6.
- The candidate is eligible for reviewer handoff.
