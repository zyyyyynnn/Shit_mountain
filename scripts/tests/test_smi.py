from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from smi_engine import core  # noqa: E402
from smi_engine.java import analyze_source as analyze_java  # noqa: E402
from smi_engine.java import component_scores as java_scores  # noqa: E402
from smi_engine.python import analyze_source as analyze_python  # noqa: E402
from smi_engine.python import component_scores as python_scores  # noqa: E402
from smi_engine.registry import get_adapters  # noqa: E402


class AdapterTests(unittest.TestCase):
    def test_known_java_scores_remain_stable(self) -> None:
        volcano_path = (
            REPO_ROOT
            / "exhibits/java/001-if-else-volcano/bad/ShitDiscountCalculator.java"
        )
        volcano_metrics = analyze_java(volcano_path.read_text(encoding="utf-8"))
        self.assertEqual(volcano_metrics.decisions, 9)
        self.assertEqual(volcano_metrics.nesting, 3)
        self.assertEqual(volcano_metrics.suspicious_comments, 2)
        self.assertEqual(sum(java_scores(volcano_metrics).values()), 73)

        god_object_path = (
            REPO_ROOT
            / "exhibits/java/002-one-class-to-rule-them-all/bad/EverythingManagerFinalV2.java"
        )
        god_metrics = analyze_java(god_object_path.read_text(encoding="utf-8"))
        self.assertEqual(god_metrics.global_mutable, 8)
        self.assertGreaterEqual(god_metrics.long_method_lines, 80)
        self.assertGreaterEqual(sum(java_scores(god_metrics).values()), 100)

    def test_java_strings_and_comments_do_not_inflate_metrics(self) -> None:
        source = """
        public class Clean {
            public static void main(String[] args) {
                String text = "if while 999 catch (Exception e)";
                // if 888
                System.out.println(text);
            }
        }
        """
        metrics = analyze_java(source)
        self.assertEqual(metrics.decisions, 0)
        self.assertEqual(metrics.magic_numbers, 0)

    def test_python_mutable_default_score_is_stable(self) -> None:
        swamp_path = (
            REPO_ROOT
            / "exhibits/python/003-mutable-default-swamp/bad/mutable_default_swamp.py"
        )
        metrics = analyze_python(swamp_path.read_text(encoding="utf-8"))
        self.assertEqual(metrics.mutable_defaults, 1)
        self.assertEqual(metrics.decisions, 1)
        self.assertEqual(metrics.nesting, 0)
        self.assertEqual(sum(python_scores(metrics).values()), 32)

    def test_python_adapter_detects_language_specific_smells(self) -> None:
        source = textwrap.dedent(
            """
            backlog = []

            def run(items=[], command="42"):
                try:
                    eval(command)
                except Exception:
                    pass
                return items
            """
        )
        metrics = analyze_python(source)
        self.assertEqual(metrics.mutable_defaults, 1)
        self.assertEqual(metrics.global_mutable, 1)
        self.assertEqual(metrics.broad_excepts, 1)
        self.assertEqual(metrics.dynamic_execution, 1)

    def test_registry_order_is_stable(self) -> None:
        self.assertEqual(
            [adapter.language for adapter in get_adapters()],
            ["java", "python"],
        )


class CoreTests(unittest.TestCase):
    def test_repository_scores_and_languages_are_stable(self) -> None:
        results = {
            result.exhibit.exhibit_id: (
                result.exhibit.display_language,
                result.score,
            )
            for result in core.analyze_all(REPO_ROOT, get_adapters())
        }
        self.assertEqual(
            results,
            {
                "000": ("Java", 1),
                "001": ("Java", 73),
                "002": ("Java", 100),
                "003": ("Python", 32),
            },
        )

    def test_leaderboard_contains_language_column(self) -> None:
        rendered = core.render_leaderboard(
            core.analyze_all(REPO_ROOT, get_adapters())
        )
        self.assertIn("| 排名 | 编号 | 展品 | 语言 | SMI |", rendered)
        self.assertIn("`mutable-default-swamp` | Python | **32**", rendered)

    def test_generated_section_replacement_is_bounded(self) -> None:
        original = (
            "before\n"
            f"{core.README_START}\n"
            "old\n"
            f"{core.README_END}\n"
            "after\n"
        )
        generated = (
            f"{core.README_START}\n"
            "new\n"
            f"{core.README_END}"
        )
        updated = core.replace_generated_section(original, generated)
        self.assertEqual(
            updated,
            (
                "before\n"
                f"{core.README_START}\n"
                "new\n"
                f"{core.README_END}\n"
                "after\n"
            ),
        )

    def test_discovery_order_is_deterministic_across_languages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "shit_demo.java").write_text(
                "public class shit_demo {}", encoding="utf-8"
            )
            java_bad = root / "exhibits/java/002-zeta/bad"
            java_bad.mkdir(parents=True)
            (java_bad / "Z.java").write_text("public class Z {}", encoding="utf-8")
            python_bad = root / "exhibits/python/001-alpha/bad"
            python_bad.mkdir(parents=True)
            (python_bad / "a.py").write_text("value = 1", encoding="utf-8")

            exhibits = core.discover_exhibits(root, get_adapters())

        self.assertEqual(
            [(exhibit.exhibit_id, exhibit.language) for exhibit in exhibits],
            [("000", "java"), ("001", "python"), ("002", "java")],
        )


if __name__ == "__main__":
    unittest.main()
