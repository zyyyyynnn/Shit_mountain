"""Stable registry for SMI language adapters."""

from __future__ import annotations

from .core import Adapter
from .java import JavaAdapter
from .python import PythonAdapter


def get_adapters() -> tuple[Adapter, ...]:
    adapters: tuple[Adapter, ...] = (JavaAdapter(), PythonAdapter())
    return tuple(sorted(adapters, key=lambda adapter: adapter.language))
