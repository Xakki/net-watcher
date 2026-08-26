import tempfile
import unittest
from pathlib import Path

from tools.verify_kanban import KanbanError, verify_board


ROOT = Path(__file__).resolve().parents[1]


class KanbanVerifierTests(unittest.TestCase):
    def test_repository_board_is_valid(self):
        verify_board(ROOT)

    def test_duplicate_identifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_board(root)
            card = next((root / ".claude/kanban/grooming").glob("NW-*.md"))
            duplicate = root / ".claude/kanban/todo" / card.name
            duplicate.write_text(card.read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(KanbanError, "duplicate"):
                verify_board(root)

    def test_foreign_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_board(root)
            card = next((root / ".claude/kanban/grooming").glob("NW-*.md"))
            card.write_text(card.read_text(encoding="utf-8") + "\nDepends on " + "TASK" + "-41.\n", encoding="utf-8")
            with self.assertRaisesRegex(KanbanError, "foreign"):
                verify_board(root)

    def test_counter_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_board(root)
            (root / ".claude/kanban.lock").write_text("prefix=NW\nNW=5\n", encoding="utf-8")
            with self.assertRaisesRegex(KanbanError, "counter"):
                verify_board(root)

    def copy_board(self, root: Path) -> None:
        source = ROOT / ".claude"
        for path in source.rglob("*"):
            target = root / path.relative_to(ROOT)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())


if __name__ == "__main__":
    unittest.main()
