"""Import an agent class from an arbitrary ``.py`` file.

The vendored ARC-AGI-3-Agents framework must be importable as ``agents`` before
the agent module is executed (agents do ``from agents.agent import Agent``).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def add_framework_to_path(root: Path) -> Path:
    vendor = root / "vendor" / "ARC-AGI-3-Agents"
    if not vendor.exists():
        raise SystemExit(
            f"Framework not found at {vendor}. Clone arcprize/ARC-AGI-3-Agents "
            "into vendor/ (see docs/02-setup-windows.md)."
        )
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    return vendor


def load_agent_class(path: Path, class_name: str):
    """Return ``class_name`` from the module at ``path``."""
    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"Agent file not found: {path}")
    spec = importlib.util.spec_from_file_location(f"arcbench_agent_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, class_name):
        raise SystemExit(f"{path.name} does not define a class named {class_name!r}")
    return getattr(module, class_name)
