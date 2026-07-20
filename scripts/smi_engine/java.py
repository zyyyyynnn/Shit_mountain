"""Java-specific metrics for the Shit Mountain Index."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .core import ExhibitSpec

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
class JavaMetrics:
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


def strip_strings_and_comments(source: str) -> str:
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


def analyze_source(source: str) -> JavaMetrics:
    clean = strip_strings_and_comments(source)
    numbers = re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", clean)
    magic_numbers = sum(float(number) not in (0, 1, -1) for number in numbers)

    declared_names = set(DECLARED_NAME_RE.findall(clean))
    opaque_names = sum(len(name) == 1 for name in declared_names)
    opaque_names += sum(
        not re.match(r"^[A-Z][A-Za-z0-9]*$", class_name)
        for class_name in CLASS_NAME_RE.findall(clean)
    )

    return JavaMetrics(
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


def aggregate_metrics(metrics: Iterable[JavaMetrics]) -> JavaMetrics:
    items = list(metrics)
    if not items:
        return JavaMetrics()
    return JavaMetrics(
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


def component_scores(metrics: JavaMetrics) -> dict[str, int]:
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


class JavaAdapter:
    language = "java"
    display_name = "Java"
    extensions = (".java",)

    def legacy_exhibits(self, root: Path) -> Sequence[ExhibitSpec]:
        legacy = root / "shit_demo.java"
        if not legacy.exists():
            return ()
        return (ExhibitSpec("000", "hello-shitmountain", (legacy,)),)

    def analyze_sources(self, sources: Sequence[Path]) -> dict[str, int]:
        metrics = aggregate_metrics(
            analyze_source(source.read_text(encoding="utf-8")) for source in sources
        )
        return component_scores(metrics)
