#!/usr/bin/env python3
"""Compatibility entrypoint for the language-adapted SMI engine."""

from smi_engine.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
