#!/usr/bin/env python3
"""Run declared exhibits in isolated temporary directories.

The runner intentionally uses only the Python standard library. It validates
`exhibit.json`, compiles each exhibit independently, applies time and output
limits, and checks the declared behavior contract.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

SCHEMA_VERSION = 1
SUPPORTED_LANGUAGES = {"java", "python"}
SUPPORTED_CONTRACTS = {"equal-output", "expected-difference", "expected-failure"}
DEFAULT_TIMEOUT_SECONDS = 5
MAX_TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 65_536


class ExhibitError(RuntimeError):
    """Raised when a manifest, execution, or contract is invalid."""


@dataclass(frozen=True)
class Variant:
    name: str
    source_dir: str
    entrypoint: str


@dataclass(frozen=True)
class Manifest:
    path: Path
    exhibit_id: str
    slug: str
    language: str
    timeout_seconds: int
    bad: Variant
    fixed: Variant
    contract: dict[str, Any]

    @property
    def directory(self) -> Path:
        return self.path.parent

    @property
    def display_name(self) -> str:
        return f"{self.exhibit_id}-{self.slug}"


@dataclass(frozen=True)
class Execution:
    variant: str
    success: bool
    phase: str
    stdout: str
    stderr: str
    returncode: int | None

    @property
    def diagnostic(self) -> str:
        parts = [self.stdout.strip(), self.stderr.strip()]
        return "\n".join(part for part in parts if part)


def _require_string(data: dict[str, Any], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExhibitError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _safe_relative_path(value: str, context: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ExhibitError(f"{context} must stay inside the exhibit directory: {value!r}")
    return path.as_posix()


def _parse_variant(data: Any, name: str) -> Variant:
    if not isinstance(data, dict):
        raise ExhibitError(f"{name} must be an object")
    source_dir = _safe_relative_path(_require_string(data, "source_dir", name), f"{name}.source_dir")
    entrypoint = _safe_relative_path(_require_string(data, "entrypoint", name), f"{name}.entrypoint")
    return Variant(name=name, source_dir=source_dir, entrypoint=entrypoint)


def load_manifest(path: Path) -> Manifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExhibitError(f"cannot read manifest {path}: {error}") from error

    if not isinstance(raw, dict):
        raise ExhibitError(f"manifest must contain a JSON object: {path}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ExhibitError(
            f"{path}: schema_version must be {SCHEMA_VERSION}, got {raw.get('schema_version')!r}"
        )

    exhibit_id = _require_string(raw, "id", str(path))
    slug = _require_string(raw, "slug", str(path))
    language = _require_string(raw, "language", str(path)).lower()
    if language not in SUPPORTED_LANGUAGES:
        raise ExhibitError(f"{path}: unsupported language {language!r}")

    timeout_seconds = raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise ExhibitError(
            f"{path}: timeout_seconds must be an integer between 1 and {MAX_TIMEOUT_SECONDS}"
        )

    contract = raw.get("contract")
    if not isinstance(contract, dict):
        raise ExhibitError(f"{path}: contract must be an object")
    contract_type = _require_string(contract, "type", f"{path}.contract")
    if contract_type not in SUPPORTED_CONTRACTS:
        raise ExhibitError(f"{path}: unsupported contract type {contract_type!r}")

    return Manifest(
        path=path,
        exhibit_id=exhibit_id,
        slug=slug,
        language=language,
        timeout_seconds=timeout_seconds,
        bad=_parse_variant(raw.get("bad"), "bad"),
        fixed=_parse_variant(raw.get("fixed"), "fixed"),
        contract=dict(contract),
    )


def discover_manifests(root: Path, language: str | None = None) -> list[Manifest]:
    manifests = [load_manifest(path) for path in sorted(root.glob("exhibits/*/*/exhibit.json"))]
    if language:
        manifests = [manifest for manifest in manifests if manifest.language == language]
    return sorted(manifests, key=lambda item: (item.exhibit_id, item.language, item.slug))


def _resolve_inside(base: Path, relative: str, context: str) -> Path:
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError as error:
        raise ExhibitError(f"{context} escapes exhibit directory: {relative!r}") from error
    return candidate


def _clean_environment(temp_dir: Path) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(temp_dir),
        "TMPDIR": str(temp_dir),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    if os.environ.get("JAVA_HOME"):
        environment["JAVA_HOME"] = os.environ["JAVA_HOME"]
    return environment


def _run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: int,
    phase: str,
    variant: str,
) -> Execution:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        return Execution(variant, False, phase, stdout, stderr + f"\ntimeout after {timeout_seconds}s", None)

    output_size = len(completed.stdout.encode("utf-8")) + len(completed.stderr.encode("utf-8"))
    if output_size > MAX_OUTPUT_BYTES:
        return Execution(
            variant,
            False,
            phase,
            completed.stdout[:MAX_OUTPUT_BYTES],
            completed.stderr + f"\noutput exceeded {MAX_OUTPUT_BYTES} bytes",
            completed.returncode,
        )

    return Execution(
        variant=variant,
        success=completed.returncode == 0,
        phase=phase,
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )


def _run_java(manifest: Manifest, variant: Variant, temp_dir: Path) -> Execution:
    source_dir = _resolve_inside(manifest.directory, variant.source_dir, f"{variant.name}.source_dir")
    sources = sorted(source_dir.rglob("*.java"))
    if not sources:
        raise ExhibitError(f"{manifest.display_name}/{variant.name}: no Java sources in {source_dir}")

    classes_dir = temp_dir / "classes"
    classes_dir.mkdir()
    environment = _clean_environment(temp_dir)
    compilation = _run_command(
        ["javac", "-encoding", "UTF-8", "-d", str(classes_dir), *map(str, sources)],
        cwd=temp_dir,
        environment=environment,
        timeout_seconds=min(manifest.timeout_seconds * 2, MAX_TIMEOUT_SECONDS),
        phase="compile",
        variant=variant.name,
    )
    if not compilation.success:
        return compilation

    return _run_command(
        ["java", "-cp", str(classes_dir), variant.entrypoint],
        cwd=temp_dir,
        environment=environment,
        timeout_seconds=manifest.timeout_seconds,
        phase="run",
        variant=variant.name,
    )


def _run_python(manifest: Manifest, variant: Variant, temp_dir: Path) -> Execution:
    source_dir = _resolve_inside(manifest.directory, variant.source_dir, f"{variant.name}.source_dir")
    if not source_dir.is_dir():
        raise ExhibitError(f"{manifest.display_name}/{variant.name}: source directory not found: {source_dir}")

    work_dir = temp_dir / "work"
    shutil.copytree(source_dir, work_dir)
    entrypoint = _resolve_inside(work_dir, variant.entrypoint, f"{variant.name}.entrypoint")
    if not entrypoint.is_file():
        raise ExhibitError(f"{manifest.display_name}/{variant.name}: entrypoint not found: {entrypoint}")

    environment = _clean_environment(temp_dir)
    compilation = _run_command(
        [sys.executable, "-m", "compileall", "-q", str(work_dir)],
        cwd=work_dir,
        environment=environment,
        timeout_seconds=min(manifest.timeout_seconds * 2, MAX_TIMEOUT_SECONDS),
        phase="compile",
        variant=variant.name,
    )
    if not compilation.success:
        return compilation

    return _run_command(
        [sys.executable, str(entrypoint)],
        cwd=work_dir,
        environment=environment,
        timeout_seconds=manifest.timeout_seconds,
        phase="run",
        variant=variant.name,
    )


def run_variant(manifest: Manifest, variant: Variant) -> Execution:
    with tempfile.TemporaryDirectory(prefix=f"shit-mountain-{manifest.exhibit_id}-{variant.name}-") as directory:
        temp_dir = Path(directory)
        if manifest.language == "java":
            return _run_java(manifest, variant, temp_dir)
        if manifest.language == "python":
            return _run_python(manifest, variant, temp_dir)
        raise ExhibitError(f"unsupported language: {manifest.language}")


def _normalized_output(execution: Execution) -> str:
    return execution.stdout.strip()


def _require_success(manifest: Manifest, execution: Execution) -> None:
    if execution.success:
        return
    raise ExhibitError(
        f"{manifest.display_name}/{execution.variant} failed during {execution.phase}:\n"
        f"{execution.diagnostic or '(no diagnostic output)'}"
    )


def verify_contract(manifest: Manifest, bad: Execution, fixed: Execution) -> None:
    contract_type = str(manifest.contract["type"])

    if contract_type == "equal-output":
        _require_success(manifest, bad)
        _require_success(manifest, fixed)
        bad_output = _normalized_output(bad)
        fixed_output = _normalized_output(fixed)
        if bad_output != fixed_output:
            raise ExhibitError(
                f"{manifest.display_name}: equal-output contract drifted: "
                f"bad={bad_output!r}, fixed={fixed_output!r}"
            )
        expected = manifest.contract.get("expected")
        if expected is not None and bad_output != str(expected):
            raise ExhibitError(
                f"{manifest.display_name}: output {bad_output!r} does not match expected {expected!r}"
            )
        return

    if contract_type == "expected-difference":
        _require_success(manifest, bad)
        _require_success(manifest, fixed)
        bad_output = _normalized_output(bad)
        fixed_output = _normalized_output(fixed)
        expected_bad = _require_string(manifest.contract, "expected_bad", "contract")
        expected_fixed = _require_string(manifest.contract, "expected_fixed", "contract")
        if bad_output != expected_bad or fixed_output != expected_fixed:
            raise ExhibitError(
                f"{manifest.display_name}: expected-difference contract failed: "
                f"bad={bad_output!r}, fixed={fixed_output!r}"
            )
        if bad_output == fixed_output:
            raise ExhibitError(f"{manifest.display_name}: expected outputs must differ")
        return

    if contract_type == "expected-failure":
        target_name = _require_string(manifest.contract, "variant", "contract")
        expected_phase = _require_string(manifest.contract, "phase", "contract")
        expected_contains = _require_string(manifest.contract, "contains", "contract")
        executions = {"bad": bad, "fixed": fixed}
        if target_name not in executions:
            raise ExhibitError("contract.variant must be 'bad' or 'fixed'")
        target = executions[target_name]
        other = executions["fixed" if target_name == "bad" else "bad"]
        if target.success:
            raise ExhibitError(f"{manifest.display_name}/{target_name}: expected failure but execution succeeded")
        if target.phase != expected_phase:
            raise ExhibitError(
                f"{manifest.display_name}/{target_name}: expected failure phase {expected_phase!r}, got {target.phase!r}"
            )
        if expected_contains not in target.diagnostic:
            raise ExhibitError(
                f"{manifest.display_name}/{target_name}: failure diagnostic does not contain {expected_contains!r}"
            )
        _require_success(manifest, other)
        expected_other = manifest.contract.get("expected_other")
        if expected_other is not None and _normalized_output(other) != str(expected_other):
            raise ExhibitError(
                f"{manifest.display_name}/{other.variant}: output does not match expected_other"
            )
        return

    raise ExhibitError(f"unsupported contract type: {contract_type}")


def run_manifest(manifest: Manifest) -> None:
    print(
        f"[exhibit] {manifest.display_name} language={manifest.language} "
        f"contract={manifest.contract['type']} timeout={manifest.timeout_seconds}s"
    )
    bad = run_variant(manifest, manifest.bad)
    fixed = run_variant(manifest, manifest.fixed)
    verify_contract(manifest, bad, fixed)
    print(
        f"[exhibit:ok] {manifest.display_name} "
        f"bad={bad.phase}:{'ok' if bad.success else 'expected-failure'} "
        f"fixed={fixed.phase}:{'ok' if fixed.success else 'expected-failure'}"
    )


def run_all(manifests: Iterable[Manifest]) -> int:
    selected = list(manifests)
    if not selected:
        raise ExhibitError("no exhibit manifests matched the requested language")
    for manifest in selected:
        run_manifest(manifest)
    print(f"[exhibit:ok] {len(selected)} exhibit contracts passed")
    return 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run isolated Shit Mountain exhibit contracts")
    parser.add_argument("--language", choices=sorted(SUPPORTED_LANGUAGES))
    parser.add_argument("--list", action="store_true", help="list manifests without executing them")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    root = Path(__file__).resolve().parents[1]
    try:
        manifests = discover_manifests(root, arguments.language)
        if arguments.list:
            for manifest in manifests:
                print(f"{manifest.display_name}\t{manifest.language}\t{manifest.contract['type']}")
            return 0
        return run_all(manifests)
    except ExhibitError as error:
        print(f"[exhibit:error] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
