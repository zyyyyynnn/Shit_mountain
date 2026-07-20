from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_repository_catalog_metadata_is_complete(self) -> None:
        items = catalog.build_items(REPO_ROOT)
        self.assertEqual(
            [(item.exhibit_id, item.title, item.score) for item in items],
            [
                ("000", "Hello Shitmountain", 1),
                ("001", "If-Else Volcano", 73),
                ("002", "One Class to Rule Them All", 100),
                ("003", "Mutable Default Argument Swamp", 32),
            ],
        )
        self.assertTrue(all(item.summary for item in items))
        self.assertTrue(all(item.smells for item in items))

    def test_readme_snapshot_has_fixed_preview_size(self) -> None:
        rendered = catalog.render_readme_snapshot(catalog.build_items(REPO_ROOT))
        preview_rows = [line for line in rendered.splitlines() if line.startswith("| [`")]
        self.assertEqual(len(preview_rows), catalog.README_PREVIEW_LIMIT)
        self.assertIn("浏览完整展品目录", rendered)
        self.assertNotIn("Hello Shitmountain", rendered)

    def test_full_catalog_contains_all_languages_and_contracts(self) -> None:
        rendered = catalog.render_catalog(catalog.build_items(REPO_ROOT))
        self.assertIn("### Java", rendered)
        self.assertIn("### Python", rendered)
        self.assertIn("`equal-output`", rendered)
        self.assertIn("`expected-difference`", rendered)
        self.assertIn("Mutable Default Argument Swamp", rendered)

    def test_readme_replacement_is_bounded(self) -> None:
        original = (
            "before\n"
            f"{catalog.README_START}\n"
            "old\n"
            f"{catalog.README_END}\n"
            "after\n"
        )
        generated = (
            f"{catalog.README_START}\n"
            "new\n"
            f"{catalog.README_END}"
        )
        self.assertEqual(
            catalog.replace_readme_snapshot(original, generated),
            (
                "before\n"
                f"{catalog.README_START}\n"
                "new\n"
                f"{catalog.README_END}\n"
                "after\n"
            ),
        )


if __name__ == "__main__":
    unittest.main()
