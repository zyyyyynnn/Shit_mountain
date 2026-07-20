from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import exhibit_runner as runner  # noqa: E402


class ManifestTests(unittest.TestCase):
    def test_repository_manifests_are_stable(self) -> None:
        root = SCRIPTS_DIR.parent
        manifests = runner.discover_manifests(root)
        self.assertEqual(
            [(item.exhibit_id, item.language, item.contract["type"]) for item in manifests],
            [
                ("001", "java", "equal-output"),
                ("002", "java", "equal-output"),
                ("003", "python", "expected-difference"),
            ],
        )

    def test_manifest_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exhibit.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id": "999",
                        "slug": "escape-tunnel",
                        "language": "python",
                        "bad": {"source_dir": "../outside", "entrypoint": "x.py"},
                        "fixed": {"source_dir": "fixed", "entrypoint": "x.py"},
                        "contract": {
                            "type": "expected-difference",
                            "expected_bad": "bad",
                            "expected_fixed": "fixed",
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(runner.ExhibitError):
                runner.load_manifest(path)


class ContractTests(unittest.TestCase):
    def manifest(self, contract: dict[str, str]) -> runner.Manifest:
        return runner.Manifest(
            path=Path("/tmp/exhibit.json"),
            exhibit_id="999",
            slug="contract-lab",
            language="python",
            timeout_seconds=5,
            bad=runner.Variant("bad", "bad", "bad.py"),
            fixed=runner.Variant("fixed", "fixed", "fixed.py"),
            contract=contract,
        )

    @staticmethod
    def execution(
        variant: str,
        *,
        success: bool = True,
        phase: str = "run",
        stdout: str = "",
        stderr: str = "",
    ) -> runner.Execution:
        return runner.Execution(
            variant=variant,
            success=success,
            phase=phase,
            stdout=stdout,
            stderr=stderr,
            returncode=0 if success else 1,
        )

    def test_equal_output_contract(self) -> None:
        manifest = self.manifest({"type": "equal-output", "expected": "same"})
        runner.verify_contract(
            manifest,
            self.execution("bad", stdout="same\n"),
            self.execution("fixed", stdout="same\n"),
        )

    def test_expected_difference_contract(self) -> None:
        manifest = self.manifest(
            {
                "type": "expected-difference",
                "expected_bad": "contaminated",
                "expected_fixed": "isolated",
            }
        )
        runner.verify_contract(
            manifest,
            self.execution("bad", stdout="contaminated"),
            self.execution("fixed", stdout="isolated"),
        )

    def test_expected_failure_contract(self) -> None:
        manifest = self.manifest(
            {
                "type": "expected-failure",
                "variant": "bad",
                "phase": "compile",
                "contains": "SyntaxError",
                "expected_other": "fixed",
            }
        )
        runner.verify_contract(
            manifest,
            self.execution(
                "bad",
                success=False,
                phase="compile",
                stderr="SyntaxError: broken geology",
            ),
            self.execution("fixed", stdout="fixed"),
        )


if __name__ == "__main__":
    unittest.main()
