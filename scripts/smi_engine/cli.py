"""Command-line interface for SMI v2."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .core import analyze_all, check_readme, render_leaderboard, write_readme
from .registry import get_adapters


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute the Shit Mountain Index")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="update README leaderboard")
    action.add_argument("--check", action="store_true", help="fail if README is stale")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    root = Path(__file__).resolve().parents[2]
    adapters = get_adapters()

    if arguments.write:
        write_readme(root, adapters)
        return 0
    if arguments.check:
        return check_readme(root, adapters)

    print(render_leaderboard(analyze_all(root, adapters)))
    return 0
