"""Collect provenance (commit SHA, dirty flag) for a result file."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=20, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip()


def git_info(root: Path) -> dict[str, object]:
    """Return ``{"sha", "dirty", "branch"}``; ``sha`` is ``"unknown"`` outside git."""
    sha = _git(root, "rev-parse", "HEAD") or "unknown"
    status = _git(root, "status", "--porcelain")
    return {
        "sha": sha,
        "dirty": bool(status) if status is not None else True,
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown",
    }
