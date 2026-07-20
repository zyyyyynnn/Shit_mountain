#!/usr/bin/env python3
"""Generate the bounded README snapshot and the complete exhibit catalog."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import exhibit_runner
from smi_engine import core
from smi_engine.registry import get_adapters

README_START = "<!-- CATALOG:START -->"
README_END = "<!-- CATALOG:END -->"
CATALOG_PATH = Path("docs/EXHIBITS.md")
README_PREVIEW_LIMIT = 3


class CatalogError(RuntimeError):
    """Raised when catalog metadata or generated documentation is invalid."""


@dataclass(frozen=True)
class CatalogMetadata:
    title: str
    summary: str
    smells: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class CatalogItem:
    exhibit_id: str
    slug: str
    language: str
    display_language: str
    title: str
    summary: str
    smells: tuple[str, ...]
    status: str
    contract: str
    score: int
    level: str
    contributors: str
    link: str


def _require_string(data: dict[str, Any], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def load_catalog_metadata(manifest: exhibit_runner.Manifest) -> CatalogMetadata:
    try:
        raw = json.loads(manifest.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"cannot read catalog metadata from {manifest.path}: {error}") from error

    catalog = raw.get("catalog")
    if not isinstance(catalog, dict):
        raise CatalogError(f"{manifest.path}: catalog must be an object")

    smells = catalog.get("smells")
    if (
        not isinstance(smells, list)
        or not smells
        or any(not isinstance(item, str) or not item.strip() for item in smells)
    ):
        raise CatalogError(f"{manifest.path}: catalog.smells must be a non-empty string array")

    return CatalogMetadata(
        title=_require_string(catalog, "title", f"{manifest.path}.catalog"),
        summary=_require_string(catalog, "summary", f"{manifest.path}.catalog"),
        smells=tuple(item.strip() for item in smells),
        status=_require_string(catalog, "status", f"{manifest.path}.catalog"),
    )


def build_items(root: Path) -> list[CatalogItem]:
    manifests = exhibit_runner.discover_manifests(root)
    manifest_by_key = {
        (manifest.exhibit_id, manifest.language, manifest.slug): manifest
        for manifest in manifests
    }
    results = core.analyze_all(root, get_adapters())
    items: list[CatalogItem] = []

    for result in results:
        exhibit = result.exhibit
        key = (exhibit.exhibit_id, exhibit.language, exhibit.slug)
        manifest = manifest_by_key.get(key)

        if manifest is None:
            items.append(
                CatalogItem(
                    exhibit_id=exhibit.exhibit_id,
                    slug=exhibit.slug,
                    language=exhibit.language,
                    display_language=exhibit.display_language,
                    title="Hello Shitmountain",
                    summary="仓库创建时留下的祖传五行 Java 样本，作为项目历史原点永久陈列。",
                    smells=("类名小写", "孤立根目录", "缺少上下文"),
                    status="永久陈列",
                    contract="历史样本",
                    score=result.score,
                    level=result.level,
                    contributors=core.top_contributors(result.components),
                    link="../shit_demo.java",
                )
            )
            continue

        metadata = load_catalog_metadata(manifest)
        relative_directory = manifest.directory.relative_to(root).as_posix()
        items.append(
            CatalogItem(
                exhibit_id=exhibit.exhibit_id,
                slug=exhibit.slug,
                language=exhibit.language,
                display_language=exhibit.display_language,
                title=metadata.title,
                summary=metadata.summary,
                smells=metadata.smells,
                status=metadata.status,
                contract=str(manifest.contract["type"]),
                score=result.score,
                level=result.level,
                contributors=core.top_contributors(result.components),
                link=f"../{relative_directory}/",
            )
        )

    return sorted(items, key=lambda item: (item.exhibit_id, item.language, item.slug))


def _ranked(items: Sequence[CatalogItem]) -> list[CatalogItem]:
    return sorted(
        items,
        key=lambda item: (-item.score, item.exhibit_id, item.language, item.slug),
    )


def render_readme_snapshot(items: Sequence[CatalogItem]) -> str:
    ranked = _ranked(items)
    languages = sorted({item.display_language for item in items})
    declared_contracts = sum(item.contract != "历史样本" for item in items)
    lines = [
        README_START,
        "<!-- Generated by scripts/catalog.py. Keep this section compact. -->",
        "",
        "## 景区概览",
        "",
        f"当前收录 **{len(items)}** 个展品，覆盖 **{len(languages)}** 种语言，"
        f"其中 **{declared_contracts}** 个正式展品拥有可执行行为合同。",
        "",
        "| 当前高风险展品 | 语言 | SMI | 景区判定 |",
        "|---|---|---:|---|",
    ]

    for item in ranked[:README_PREVIEW_LIMIT]:
        lines.append(
            f"| [`{item.exhibit_id} · {item.title}`]({item.link.removeprefix('../')}) | "
            f"{item.display_language} | **{item.score}** | {item.level} |"
        )

    lines.extend(
        [
            "",
            "[浏览完整展品目录](docs/EXHIBITS.md) · "
            "[查看 SMI 规则与完整排行榜](docs/SMI.md)",
            README_END,
        ]
    )
    return "\n".join(lines)


def render_catalog(items: Sequence[CatalogItem]) -> str:
    languages = sorted({item.display_language for item in items})
    ranked = _ranked(items)
    lines = [
        "# 展品目录 / Exhibit Catalog",
        "",
        "> 本页由 `python3 scripts/catalog.py --write` 生成。请修改各展品的 `exhibit.json`，不要直接编辑表格。",
        "",
        "## 总览",
        "",
        f"- 展品数量：**{len(items)}**",
        f"- 语言数量：**{len(languages)}**",
        f"- 当前最高 SMI：**{ranked[0].score if ranked else 0}**",
        "",
        "| 编号 | 展品 | 语言 | 主要异味 | 合同 | SMI | 状态 |",
        "|---:|---|---|---|---|---:|---|",
    ]

    for item in items:
        smells = "、".join(item.smells)
        lines.append(
            f"| `{item.exhibit_id}` | [`{item.title}`]({item.link}) | "
            f"{item.display_language} | {smells} | `{item.contract}` | "
            f"**{item.score}** | {item.status} |"
        )

    lines.extend(["", "## 按语言浏览", ""])
    for language in languages:
        language_items = [item for item in items if item.display_language == language]
        lines.extend([f"### {language}", ""])
        for item in language_items:
            lines.extend(
                [
                    f"#### `{item.exhibit_id}` · [{item.title}]({item.link})",
                    "",
                    item.summary,
                    "",
                    f"- 主要异味：{'、'.join(item.smells)}",
                    f"- 行为合同：`{item.contract}`",
                    f"- SMI：**{item.score}**，{item.level}",
                    f"- 主要计分来源：{item.contributors}",
                    f"- 展区状态：{item.status}",
                    "",
                ]
            )

    lines.extend(
        [
            "## 维护方式",
            "",
            "新增正式展品时，只需在 `exhibit.json` 中维护 `catalog` 元数据，并执行：",
            "",
            "```bash",
            "python3 scripts/catalog.py --write",
            "python3 scripts/smi.py --write",
            "```",
            "",
            "README 只展示固定数量的高风险展品，因此展品增长不会继续拉长项目首页。",
        ]
    )
    return "\n".join(lines) + "\n"


def replace_readme_snapshot(readme: str, generated: str) -> str:
    if README_START not in readme or README_END not in readme:
        raise CatalogError(
            f"README must contain both {README_START!r} and {README_END!r}"
        )
    start = readme.index(README_START)
    end = readme.index(README_END, start) + len(README_END)
    return readme[:start] + generated + readme[end:]


def expected_files(root: Path) -> dict[Path, str]:
    items = build_items(root)
    readme_path = root / "README.md"
    current_readme = readme_path.read_text(encoding="utf-8")
    return {
        readme_path: replace_readme_snapshot(
            current_readme,
            render_readme_snapshot(items),
        ),
        root / CATALOG_PATH: render_catalog(items),
    }


def write_files(root: Path) -> None:
    for path, content in expected_files(root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[catalog] updated {path.relative_to(root)}")


def check_files(root: Path) -> int:
    stale = False
    for path, expected in expected_files(root).items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            print(f"[catalog] current: {path.relative_to(root)}")
            continue

        stale = True
        print(
            f"[catalog] stale: {path.relative_to(root)}; "
            "run python3 scripts/catalog.py --write"
        )
        difference = difflib.unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile=str(path.relative_to(root)),
            tofile=f"{path.relative_to(root)} (generated)",
            lineterm="",
        )
        print("\n".join(difference))
    return 1 if stale else 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maintain the exhibit catalog")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="update generated catalog files")
    action.add_argument("--check", action="store_true", help="fail when catalog files are stale")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    root = Path(__file__).resolve().parents[1]
    try:
        if arguments.write:
            write_files(root)
            return 0
        return check_files(root)
    except (CatalogError, exhibit_runner.ExhibitError, ValueError) as error:
        print(f"[catalog:error] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
