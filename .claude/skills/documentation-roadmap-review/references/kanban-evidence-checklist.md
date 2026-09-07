# Kanban Evidence Checklist

Use this checklist when a roadmap diff changes lifecycle or priority claims.

- Record `git status --short --branch`, baseline-to-HEAD diff stat, changed files,
  and `git diff --check`.
- For each changed slug, confirm the matching card path and lifecycle directory.
- Read the card's dependencies and acceptance criteria before accepting a
  sequence such as `A → B → C`.
- Search every new wiki-style link and confirm it resolves to the intended card.
- Distinguish current pilot evidence from future rollout gates. A card may be in
  `ready/` for review while rollback/reclaim or production-scale checks remain
  mandatory.
- Re-run the snapshot immediately before the verdict; report files changed as
  “none” for a read-only review.
