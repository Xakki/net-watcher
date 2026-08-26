### Establish standalone project governance

**Criticality:** Blocking

**TAGS:**
- governance
- security

**Description:**
Create a self-contained public governance, publication-boundary, documentation, and verification baseline.

**Problem:**
The repository needs public-safe instructions, tasks, policies, manifests, and enforceable checks without inheriting private project state.

**Impact:**
Without this baseline, review and publication decisions are not reliably bounded.

**Recommendation:**
Maintain exact tracked and served allowlists, local NW cards, deny-first agent settings, neutral documentation, and mutation-tested verifiers.

**Acceptance Criteria:**
- All six Kanban stages and NW-1 through NW-6 validate locally.
- Documentation and agent instructions define the no-data and publication boundaries.
- Verifiers enforce tracked files, bounded reads, ignored local state, and disclosure detection.
- JSON, unit, lint, verify, build, and feasible smoke gates pass.
- The provider remains unset and publication remains unauthorized.

**Decisions:**
- Independent review is required before this card can advance beyond test.

**Review verdict:**
- PASS. Independent review confirmed four targeted cases, five boundary behaviors, and all 57 verification tests.
- Local verification passed; publication remains blocked by the unset provider and separate human authorization.
