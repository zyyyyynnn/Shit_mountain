from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import smi  # noqa: E402


VOLCANO = """public class ShitDiscountCalculator {
    public static int calculate(int p, String t, boolean f, int c) {
        int x = p;

        // 简单处理一下
        if (t.equals("VIP")) {
            if (p > 100) {
                if (f) {
                    x = p - 30;
                } else {
                    x = p - 20;
                }
            } else {
                x = p - 5;
            }
        } else {
            if (t.equals("NORMAL")) {
                if (f) {
                    x = p - 3;
                } else {
                    x = p;
                }
            } else {
                x = p;
            }
        }

        if (c == 1) {
            x = x - 10;
        }
        if (c == 2) {
            x = x - 20;
        }
        if (c == 999) {
            x = x - 1; // 没人知道为什么，但删了测试就红
        }

        if (x < 0) {
            x = 0;
        }
        return x;
    }

    public static void main(String[] args) {
        System.out.println(calculate(120, "VIP", true, 2));
    }
}
"""


class AnalyzerTests(unittest.TestCase):
    def test_known_volcano_score_is_stable(self) -> None:
        metrics = smi.analyze_java(VOLCANO)
        components = smi.component_scores(metrics)

        self.assertEqual(metrics.decisions, 9)
        self.assertEqual(metrics.nesting, 3)
        self.assertEqual(metrics.suspicious_comments, 2)
        self.assertEqual(sum(components.values()), 73)
        self.assertEqual(smi.danger_level(73), "铲屎车进入一级战备")

    def test_known_god_object_score_is_stable(self) -> None:
        source_path = (
            REPO_ROOT
            / "exhibits/java/002-one-class-to-rule-them-all/bad/EverythingManagerFinalV2.java"
        )
        exhibit = smi.Exhibit(
            exhibit_id="002",
            slug="one-class-to-rule-them-all",
            sources=(source_path,),
        )
        result = smi.analyze_exhibit(exhibit)

        self.assertEqual(result.metrics.global_mutable, 8)
        self.assertGreaterEqual(result.metrics.long_method_lines, 80)
        self.assertEqual(result.score, 100)
        self.assertEqual(result.level, "建议原地成立事故调查组")

    def test_strings_and_comments_do_not_inflate_metrics(self) -> None:
        source = """
        public class Clean {
            public static void main(String[] args) {
                String text = "if while 999 catch (Exception e)";
                // if 888
                System.out.println(text);
            }
        }
        """
        metrics = smi.analyze_java(source)

        self.assertEqual(metrics.decisions, 0)
        self.assertEqual(metrics.magic_numbers, 0)

    def test_generated_section_replacement_is_bounded(self) -> None:
        original = (
            "before\n"
            f"{smi.README_START}\n"
            "old\n"
            f"{smi.README_END}\n"
            "after\n"
        )
        generated = (
            f"{smi.README_START}\n"
            "new\n"
            f"{smi.README_END}"
        )

        updated = smi.replace_generated_section(original, generated)

        self.assertEqual(
            updated,
            (
                "before\n"
                f"{smi.README_START}\n"
                "new\n"
                f"{smi.README_END}\n"
                "after\n"
            ),
        )

    def test_discovery_order_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "shit_demo.java").write_text("public class shit_demo {}", encoding="utf-8")
            bad = root / "exhibits/java/002-zeta/bad"
            bad.mkdir(parents=True)
            (bad / "Z.java").write_text("public class Z {}", encoding="utf-8")
            bad = root / "exhibits/java/001-alpha/bad"
            bad.mkdir(parents=True)
            (bad / "A.java").write_text("public class A {}", encoding="utf-8")

            exhibits = smi.discover_exhibits(root)

        self.assertEqual(
            [exhibit.exhibit_id for exhibit in exhibits],
            ["000", "001", "002"],
        )


if __name__ == "__main__":
    unittest.main()
