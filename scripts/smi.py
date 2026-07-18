#!/usr/bin/env python3
"""Compute the Shit Mountain Index (SMI) and maintain the README leaderboard.

The analyzer is intentionally deterministic and dependency-free. It uses
transparent heuristics rather than pretending to be a full Java parser.
"""

from __future__ import annotations

import argparse
import difflib
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

README_START = "<!-- SMI:START -->"
README_END = "<!-- SMI:END -->"

SUSPICIOUS_COMMENT_RE = re.compile(
    r"(简单|临时|先这样|没人知道|不要动|删了.*红|"
    r"temporary|quick\s*fix|hack|todo|do\s*not\s*touch|works?\s*for\s*now)",
    re.IGNORECASE,
)
CONTROL_RE = re.compile(r"\b(?:if|for|while|case|catch)\b")
CATCH_ALL_RE = re.compile(
    r"\bcatch\s*\(\s*(?:final\s+)?(?:Exception|Throwable)\b"
)
EMPTY_CATCH_RE = re.compile(r"\bcatch\s*\([^)]*\)\s*\{\s*\}", re.DOTALL)
DECLARED_NAME_RE = re.compile(
    r"\b(?:byte|short|int|long|float|double|boolean|char|String|Object|var)"
    r"\s+([A-Za-z_]\w*)"
)
CLASS_NAME_RE = re.compile(r"\bpublic\s+class\s+([A-Za-z_]\w*)")
METHOD_START_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|static|final|synchronized|native|"
    r"abstract|strictfp)\s+)*"
    r"(?:[A-Za-z_][\w<>\[\], ?]*\s+)+([A-Za-z_]\w*)"
    r"\s*\([^;{}]*\)\s*\{"
)


@dataclass(frozen=True)
class Metrics:
    decisions: int = 0
    nesting: int = 0
    magic_numbers: int = 0
    opaque_names: int = 0
    long_method_lines: int = 0
    global_mutable: int = 0
    catch_all: int = 0
    empty_catch: int = 0
    suspicious_comments: int = 0
    duplicate_statements: int = 0


@dataclass(frozen=True)
class Exhibit:
    exhibit_id: str
    slug: str
    sources: tuple[Path, ...]


@dataclass(frozen=True)
class Result:
    exhibit: Exhibit
    metrics: Metrics
    components: dict[str, int]
    score: int
    level: str


def strip_strings_and_comments(source: str) -> str:
    """Remove strings and comments while preserving line count."""
    result = re.sub(
        r"/\*.*?\*/",
        lambda match: "\n" * match.group(0).count("\n"),
        source,
        flags=re.DOTALL,
    )
    result = re.sub(r"//[^\n]*", "", result)
    result = re.sub(r'"(?:\\.|[^"\\])*"', '""', result)
    result = re.sub(r"'(?:\\.|[^'\\])*'", "''", result)
    return result


def extract_comments(source: str) -> list[str]:
    matches = re.findall(r"//([^\n]*)|/\*(.*?)\*/", source, flags=re.DOTALL)
    return [line_comment or block_comment for line_comment, block_comment in matches]


def maximum_brace_depth(clean_source: str) -> int:
    depth = 0
    maximum = 0
    for character in clean_source:
        if character == "{":
            depth += 1
            maximum = max(maximum, depth)
        elif character == "}":
            depth = max(0, depth - 1)
    return maximum


def maximum_method_length(source: str) -> int:
    lines = source.splitlines()
    maximum = 0
    index = 0

    while index < len(lines):
        if not METHOD_START_RE.match(lines[index]):
            index += 1
            continue

        depth = 0
        started = False
        end = index

        while end < len(lines):
            clean_line = strip_strings_and_comments(lines[end])
            for character in clean_line:
                if character == "{":
                    depth += 1
                    started = True
                elif character == "}":
                    depth -= 1
            if started and depth == 0:
                maximum = max(maximum, end - index + 1)
                break
            end += 1

        index = max(index + 1, end + 1)

    return maximum


def count_global_mutable_fields(clean_source: str) -> int:
    depth = 0
    count = 0

    for line in clean_source.splitlines():
        stripped = line.strip()
        if (
            depth == 1
            and ";" in stripped
            and "(" not in stripped
            and not re.search(r"\bstatic\s+final\b", stripped)
            and not stripped.startswith(("import ", "package "))
        ):
            count += 1
        depth += line.count("{") - line.count("}")

    return count


def count_duplicate_statements(clean_source: str) -> int:
    statements: Counter[str] = Counter()

    for line in clean_source.splitlines():
        normalized = re.sub(r"\s+", " ", line.strip())
        if len(normalized) < 10 or normalized in {"{", "}"}:
            continue
        if normalized.startswith(
            ("import ", "package ", "public class ", "class ", "interface ", "enum ", "@")
        ):
            continue
        if METHOD_START_RE.match(normalized):
            continue
        if normalized.endswith("{") or normalized.startswith("else"):
            continue
        statements[normalized] += 1

    return sum(count - 1 for count in statements.values() if count > 1)


def analyze_java(source: str) -> Metrics:
    clean = strip_strings_and_comments(source)
    numbers = re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", clean)
    magic_numbers = sum(float(number) not in (0, 1, -1) for number in numbers)

    declared_names = set(DECLARED_NAME_RE.findall(clean))
    opaque_names = sum(len(name) == 1 for name in declared_names)
    opaque_names += sum(
        not re.match(r"^[A-Z][A-Za-z0-9]*$", class_name)
        for class_name in CLASS_NAME_RE.findall(clean)
    )

    return Metrics(
        decisions=(
            len(CONTROL_RE.findall(clean))
            + clean.count("&&")
            + clean.count("||")
            + clean.count("?")
        ),
        nesting=max(0, maximum_brace_depth(clean) - 2),
        magic_numbers=magic_numbers,
        opaque_names=opaque_names,
        long_method_lines=maximum_method_length(source),
        global_mutable=count_global_mutable_fields(clean),
        catch_all=len(CATCH_ALL_RE.findall(clean)),
        empty_catch=len(EMPTY_CATCH_RE.findall(clean)),
        suspicious_comments=sum(
            bool(SUSPICIOUS_COMMENT_RE.search(comment))
            for comment in extract_comments(source)
        ),
        duplicate_statements=count_duplicate_statements(clean),
    )


def aggregate_metrics(metrics: Iterable[Metrics]) -> Metrics:
    items = list(metrics)
    if not items:
        return Metrics()

    return Metrics(
        decisions=sum(item.decisions for item in items),
        nesting=max(item.nesting for item in items),
        magic_numbers=sum(item.magic_numbers for item in items),
        opaque_names=sum(item.opaque_names for item in items),
        long_method_lines=max(item.long_method_lines for item in items),
        global_mutable=sum(item.global_mutable for item in items),
        catch_all=sum(item.catch_all for item in items),
        empty_catch=sum(item.empty_catch for item in items),
        suspicious_comments=sum(item.suspicious_comments for item in items),
        duplicate_statements=sum(item.duplicate_statements for item in items),
    )


def component_scores(metrics: Metrics) -> dict[str, int]:
    return {
        "决策点": min(metrics.decisions * 2, 24),
        "嵌套深度": min(metrics.nesting * 4, 16),
        "魔法数字": min(metrics.magic_numbers * 2, 20),
        "含糊命名": min(metrics.opaque_names, 10),
        "超长方法": min(
            max(0, math.ceil((metrics.long_method_lines - 25) / 5)) * 2,
            16,
        ),
        "全局可变状态": min(metrics.global_mutable * 6, 18),
        "宽泛异常捕获": min(
            metrics.catch_all * 8 + metrics.empty_catch * 6,
            20,
        ),
        "可疑注释": min(metrics.suspicious_comments * 5, 15),
        "重复语句": min(metrics.duplicate_statements * 3, 15),
    }


def danger_level(score: int) -> str:
    if score <= 20:
        return "轻微异味，可步行参观"
    if score <= 50:
        return "建议佩戴防护设备"
    if score <= 80:
        return "铲屎车进入一级战备"
    return "建议原地成立事故调查组"


def discover_exhibits(root: Path) -> list[Exhibit]:
    exhibits: list[Exhibit] = []
    legacy = root / "shit_demo.java"
    if legacy.exists():
        exhibits.append(
            Exhibit(
                exhibit_id="000",
                slug="hello-shitmountain",
                sources=(legacy,),
            )
        )

    for bad_directory in sorted(root.glob("exhibits/*/*/bad")):
        exhibit_directory = bad_directory.parent
        if "-" in exhibit_directory.name:
            exhibit_id, slug = exhibit_directory.name.split("-", 1)
        else:
            exhibit_id, slug = "???", exhibit_directory.name

        sources = tuple(sorted(bad_directory.rglob("*.java")))
        if sources:
            exhibits.append(
                Exhibit(
                    exhibit_id=exhibit_id,
                    slug=slug,
                    sources=sources,
                )
            )

    return exhibits


def analyze_exhibit(exhibit: Exhibit) -> Result:
    metrics = aggregate_metrics(
        analyze_java(source.read_text(encoding="utf-8"))
        for source in exhibit.sources
    )
    components = component_scores(metrics)
    score = min(sum(components.values()), 100)
    return Result(
        exhibit=exhibit,
        metrics=metrics,
        components=components,
        score=score,
        level=danger_level(score),
    )


def top_contributors(components: dict[str, int], limit: int = 3) -> str:
    ranked = sorted(
        ((name, value) for name, value in components.items() if value),
        key=lambda item: (-item[1], item[0]),
    )
    if not ranked:
        return "未检测到显著异味"
    return " / ".join(f"{name} {value}" for name, value in ranked[:limit])


def render_leaderboard(results: Sequence[Result]) -> str:
    ranked = sorted(
        results,
        key=lambda result: (-result.score, result.exhibit.exhibit_id, result.exhibit.slug),
    )
    lines = [
        README_START,
        "<!-- Generated by scripts/smi.py. Manual edits inside this block will be overwritten. -->",
        "",
        "### 当前排行榜",
        "",
        "| 排名 | 编号 | 展品 | SMI | 景区判定 | 主要贡献 |",
        "|---:|---:|---|---:|---|---|",
    ]
    for position, result in enumerate(ranked, start=1):
        lines.append(
            f"| {position} | `{result.exhibit.exhibit_id}` | "
            f"`{result.exhibit.slug}` | **{result.score}** | "
            f"{result.level} | {top_contributors(result.components)} |"
        )

    lines.extend(
        [
            "",
            "> SMI 仅用于教育、娱乐和代码审查训练，不用于评价开发者能力或工作绩效。",
            README_END,
        ]
    )
    return "\n".join(lines)


def replace_generated_section(readme: str, generated: str) -> str:
    if README_START not in readme or README_END not in readme:
        raise ValueError(
            f"README must contain both {README_START!r} and {README_END!r}"
        )

    start = readme.index(README_START)
    end = readme.index(README_END, start) + len(README_END)
    return readme[:start] + generated + readme[end:]


def expected_readme(root: Path) -> str:
    readme_path = root / "README.md"
    current = readme_path.read_text(encoding="utf-8")
    results = [analyze_exhibit(exhibit) for exhibit in discover_exhibits(root)]
    return replace_generated_section(current, render_leaderboard(results))


def write_readme(root: Path) -> None:
    readme_path = root / "README.md"
    updated = expected_readme(root)
    readme_path.write_text(updated, encoding="utf-8")
    print(f"[smi] updated {readme_path.relative_to(root)}")


def check_readme(root: Path) -> int:
    readme_path = root / "README.md"
    current = readme_path.read_text(encoding="utf-8")
    expected = expected_readme(root)
    if current == expected:
        print("[smi] leaderboard is current")
        return 0

    print("[smi] README leaderboard is stale; run: python3 scripts/smi.py --write")
    difference = difflib.unified_diff(
        current.splitlines(),
        expected.splitlines(),
        fromfile="README.md",
        tofile="README.md (generated)",
        lineterm="",
    )
    print("\n".join(difference))
    return 1


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute the Shit Mountain Index")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="update README leaderboard")
    action.add_argument("--check", action="store_true", help="fail if README is stale")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    root = Path(__file__).resolve().parents[1]

    if arguments.write:
        write_readme(root)
        return 0
    if arguments.check:
        return check_readme(root)

    results = [analyze_exhibit(exhibit) for exhibit in discover_exhibits(root)]
    print(render_leaderboard(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
