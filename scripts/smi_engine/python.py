"""Python-specific AST and token metrics for the Shit Mountain Index."""

from __future__ import annotations

import ast
import io
import math
import re
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .core import ExhibitSpec

SUSPICIOUS_COMMENT_RE = re.compile(
    r"(简单|临时|先这样|没人知道|不要动|"
    r"temporary|quick\s*fix|hack|todo|do\s*not\s*touch|works?\s*for\s*now)",
    re.IGNORECASE,
)
MUTABLE_FACTORIES = {"list", "dict", "set", "defaultdict"}
DYNAMIC_CALLS = {"eval", "exec"}


@dataclass(frozen=True)
class PythonMetrics:
    decisions: int = 0
    nesting: int = 0
    magic_numbers: int = 0
    mutable_defaults: int = 0
    global_mutable: int = 0
    broad_excepts: int = 0
    bare_excepts: int = 0
    long_function_lines: int = 0
    dynamic_execution: int = 0
    suspicious_comments: int = 0
    duplicate_statements: int = 0


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_mutable_value(node: ast.AST | None) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    if isinstance(node, ast.Call):
        return _call_name(node.func) in MUTABLE_FACTORIES
    return False


def count_decisions(tree: ast.AST) -> int:
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if not _is_main_guard(node):
                count += 1
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.IfExp)):
            count += 1
        elif isinstance(node, ast.Try):
            count += len(node.handlers)
        elif isinstance(node, ast.Match):
            count += len(node.cases)
        elif isinstance(node, ast.BoolOp):
            count += max(0, len(node.values) - 1)
        elif isinstance(node, ast.comprehension):
            count += 1 + len(node.ifs)
    return count


class _NestingVisitor(ast.NodeVisitor):
    control_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
        ast.Match,
    )

    def __init__(self) -> None:
        self.depth = 0
        self.maximum = 0

    def generic_visit(self, node: ast.AST) -> None:
        is_control = isinstance(node, self.control_nodes)
        if isinstance(node, ast.If) and _is_main_guard(node):
            is_control = False
        if is_control:
            self.depth += 1
            self.maximum = max(self.maximum, self.depth)
            ast.NodeVisitor.generic_visit(self, node)
            self.depth -= 1
            return
        ast.NodeVisitor.generic_visit(self, node)


def maximum_nesting(tree: ast.AST) -> int:
    visitor = _NestingVisitor()
    visitor.visit(tree)
    return visitor.maximum


def count_mutable_defaults(tree: ast.AST) -> int:
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        defaults: list[ast.AST | None] = [*node.args.defaults, *node.args.kw_defaults]
        count += sum(_is_mutable_value(default) for default in defaults)
    return count


def count_global_mutable(tree: ast.Module) -> int:
    count = 0
    for node in tree.body:
        if isinstance(node, ast.Assign):
            count += _is_mutable_value(node.value)
        elif isinstance(node, ast.AnnAssign):
            count += _is_mutable_value(node.value)
    return count


def count_magic_numbers(tree: ast.AST) -> int:
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        value = node.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if value not in (-1, 0, 1):
            count += 1
    return count


def maximum_function_length(tree: ast.AST) -> int:
    lengths = [
        max(0, (node.end_lineno or node.lineno) - node.lineno + 1)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return max(lengths, default=0)


def count_exception_smells(tree: ast.AST) -> tuple[int, int]:
    broad = 0
    bare = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            bare += 1
        elif _call_name(node.type) in {"Exception", "BaseException"}:
            broad += 1
    return broad, bare


def count_dynamic_execution(tree: ast.AST) -> int:
    return sum(
        isinstance(node, ast.Call) and _call_name(node.func) in DYNAMIC_CALLS
        for node in ast.walk(tree)
    )


def count_suspicious_comments(source: str) -> int:
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        return sum(
            token.type == tokenize.COMMENT
            and bool(SUSPICIOUS_COMMENT_RE.search(token.string))
            for token in tokens
        )
    except tokenize.TokenError:
        return 0


def count_duplicate_statements(tree: ast.AST) -> int:
    statements: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return)):
            continue
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        statements[ast.dump(node, include_attributes=False)] += 1
    return sum(count - 1 for count in statements.values() if count > 1)


def analyze_source(source: str) -> PythonMetrics:
    tree = ast.parse(source)
    broad_excepts, bare_excepts = count_exception_smells(tree)
    return PythonMetrics(
        decisions=count_decisions(tree),
        nesting=maximum_nesting(tree),
        magic_numbers=count_magic_numbers(tree),
        mutable_defaults=count_mutable_defaults(tree),
        global_mutable=count_global_mutable(tree),
        broad_excepts=broad_excepts,
        bare_excepts=bare_excepts,
        long_function_lines=maximum_function_length(tree),
        dynamic_execution=count_dynamic_execution(tree),
        suspicious_comments=count_suspicious_comments(source),
        duplicate_statements=count_duplicate_statements(tree),
    )


def aggregate_metrics(metrics: Iterable[PythonMetrics]) -> PythonMetrics:
    items = list(metrics)
    if not items:
        return PythonMetrics()
    return PythonMetrics(
        decisions=sum(item.decisions for item in items),
        nesting=max(item.nesting for item in items),
        magic_numbers=sum(item.magic_numbers for item in items),
        mutable_defaults=sum(item.mutable_defaults for item in items),
        global_mutable=sum(item.global_mutable for item in items),
        broad_excepts=sum(item.broad_excepts for item in items),
        bare_excepts=sum(item.bare_excepts for item in items),
        long_function_lines=max(item.long_function_lines for item in items),
        dynamic_execution=sum(item.dynamic_execution for item in items),
        suspicious_comments=sum(item.suspicious_comments for item in items),
        duplicate_statements=sum(item.duplicate_statements for item in items),
    )


def component_scores(metrics: PythonMetrics) -> dict[str, int]:
    return {
        "决策点": min(metrics.decisions * 2, 24),
        "嵌套深度": min(metrics.nesting * 4, 16),
        "魔法数字": min(metrics.magic_numbers * 2, 20),
        "可变默认参数": min(metrics.mutable_defaults * 30, 30),
        "全局可变状态": min(metrics.global_mutable * 8, 24),
        "宽泛异常捕获": min(
            metrics.broad_excepts * 10 + metrics.bare_excepts * 12,
            24,
        ),
        "超长函数": min(
            max(0, math.ceil((metrics.long_function_lines - 25) / 5)) * 2,
            16,
        ),
        "动态执行": min(metrics.dynamic_execution * 20, 40),
        "可疑注释": min(metrics.suspicious_comments * 5, 15),
        "重复语句": min(metrics.duplicate_statements * 3, 15),
    }


class PythonAdapter:
    language = "python"
    display_name = "Python"
    extensions = (".py",)

    def legacy_exhibits(self, root: Path) -> Sequence[ExhibitSpec]:
        return ()

    def analyze_sources(self, sources: Sequence[Path]) -> dict[str, int]:
        metrics = aggregate_metrics(
            analyze_source(source.read_text(encoding="utf-8")) for source in sources
        )
        return component_scores(metrics)
