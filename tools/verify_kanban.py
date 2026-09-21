#!/usr/bin/env python3
import re
import sys
from pathlib import Path

try:
    from tools.verify_site import read_bounded
except ModuleNotFoundError:
    from verify_site import read_bounded

STAGES = ("grooming", "todo", "progress", "test", "ready", "done")
REQUIRED_SECTIONS = (
    "**Criticality:**",
    "**TAGS:**",
    "**Description:**",
    "**Problem:**",
    "**Impact:**",
    "**Recommendation:**",
    "**Acceptance Criteria:**",
)
EXPECTED_STAGES = {
    **{f"NW-{number}": "done" for number in (1, 2, 3, 4, 5, 7, 8)},
    **{f"NW-{number}": "grooming" for number in (6,)},
}


class KanbanError(ValueError):
    pass


def verify_board(root: Path) -> None:
    board = root / ".claude" / "kanban"
    missing_dirs = [stage for stage in STAGES if not (board / stage).is_dir()]
    if missing_dirs:
        raise KanbanError(f"missing stages: {missing_dirs}")
    lock_lines = (root / ".claude" / "kanban.lock").read_text(encoding="utf-8").splitlines()
    if lock_lines != ["prefix=NW", "NW=8"]:
        raise KanbanError("prefix or counter drift")
    seen: dict[str, str] = {}
    errors: list[str] = []
    cards = []
    for stage in STAGES:
        cards.extend((stage, path) for path in sorted((board / stage).glob("*.md")))
    for stage, path in cards:
        match = re.fullmatch(r"(NW-[1-8])-[a-z0-9]+(?:-[a-z0-9]+)*\.md", path.name)
        if not match:
            errors.append(f"invalid filename: {path.name}")
            continue
        card_id = match.group(1)
        if card_id in seen:
            errors.append(f"duplicate identifier: {card_id}")
        seen[card_id] = stage
        if EXPECTED_STAGES[card_id] != stage:
            errors.append(f"wrong stage for {card_id}")
        text = read_bounded(path)
        if not text.startswith("### "):
            errors.append(f"missing title: {card_id}")
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"missing required section in {card_id}: {section}")
        if stage == "grooming" and "**Open questions:**" not in text:
            errors.append(f"missing open questions: {card_id}")
        if stage != "grooming" and "**Open questions:**" in text:
            errors.append(f"open questions outside grooming: {card_id}")
        foreign = re.search(r"\b(?:EPIC|TASK|TICKET|MYIP|ARIN)[-_ ]?\d+\b", text, re.IGNORECASE)
        if foreign:
            errors.append(f"foreign identifier in {card_id}")
        if re.search(r"/(?:home|users|workspace)/", text, re.IGNORECASE):
            errors.append(f"internal path in {card_id}")
        if re.search(r"\b[0-9a-f]{40}\b", text, re.IGNORECASE):
            errors.append(f"commit identifier in {card_id}")
        for dependency in re.findall(r"\bNW-(\d+)\b", text, re.IGNORECASE):
            if not 1 <= int(dependency) <= 8:
                errors.append(f"invalid dependency in {card_id}")
    if set(seen) != set(EXPECTED_STAGES):
        errors.append(f"card set mismatch: {sorted(seen)}")
    if errors:
        raise KanbanError("; ".join(errors))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        verify_board(root)
    except (KanbanError, ValueError) as error:
        print(f"kanban verification failed: {error}", file=sys.stderr)
        return 1
    print("kanban verification passed: 8 cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
