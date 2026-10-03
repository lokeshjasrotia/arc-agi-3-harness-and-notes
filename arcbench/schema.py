"""Result-file schema and validation.

Project rule: *a performance number that is not backed by a committed result
file carrying the git SHA, the split and the exact command does not exist.*
``validate_result`` is the single place that rule is enforced.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = 1

#: Where a number came from. Local runs and Kaggle runs are never mixed.
ALLOWED_SPLITS = ("public-local", "kaggle-public-lb", "kaggle-private")

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_TOP_LEVEL_KEYS = (
    "schema_version",
    "created_utc",
    "agent",
    "git",
    "split",
    "command",
    "environment",
    "config",
    "games",
    "aggregate",
)
_GAME_KEYS = ("game_id", "seed", "state", "levels_completed", "actions", "wall_seconds")


class ResultError(ValueError):
    """Raised when a result file violates the schema or the provenance rules."""


def validate_result(doc: dict[str, Any]) -> None:
    """Raise :class:`ResultError` unless ``doc`` is a well-formed, traceable result."""
    if not isinstance(doc, dict):
        raise ResultError("result must be a JSON object")
    missing = [k for k in _TOP_LEVEL_KEYS if k not in doc]
    if missing:
        raise ResultError(f"missing top-level keys: {missing}")
    if doc["schema_version"] != SCHEMA_VERSION:
        raise ResultError(
            f"unsupported schema_version {doc['schema_version']!r} "
            f"(expected {SCHEMA_VERSION})"
        )

    sha = (doc["git"] or {}).get("sha", "")
    if not isinstance(sha, str) or not _SHA_RE.match(sha):
        raise ResultError(
            "git.sha must be a full 40-character commit hash; a result without "
            "a SHA does not count as evidence"
        )
    if "dirty" not in doc["git"]:
        raise ResultError("git.dirty must be recorded")

    if doc["split"] not in ALLOWED_SPLITS:
        raise ResultError(f"split must be one of {ALLOWED_SPLITS}, got {doc['split']!r}")
    if not isinstance(doc["command"], str) or not doc["command"].strip():
        raise ResultError("command must be the exact, non-empty command that was run")
    if not (doc["agent"] or {}).get("name"):
        raise ResultError("agent.name is required")

    games = doc["games"]
    if not isinstance(games, list) or not games:
        raise ResultError("games must be a non-empty list")
    for i, g in enumerate(games):
        gm = [k for k in _GAME_KEYS if k not in g]
        if gm:
            raise ResultError(f"games[{i}] missing keys: {gm}")
        if g["levels_completed"] < 0 or g["actions"] < 0:
            raise ResultError(f"games[{i}] has negative counters")


def aggregate(games: list[dict[str, Any]], scorecard_score: float | None) -> dict[str, Any]:
    """Summarise per-game rows. ``scorecard_score`` is the engine's own score."""
    n = len(games)
    levels = sum(int(g["levels_completed"]) for g in games)
    return {
        "runs": n,
        "total_levels_completed": levels,
        "mean_levels_completed": round(levels / n, 4) if n else 0.0,
        "wins": sum(1 for g in games if str(g["state"]).endswith("WIN")),
        "errors": sum(1 for g in games if g.get("error")),
        "total_actions": sum(int(g["actions"]) for g in games),
        "total_wall_seconds": round(sum(float(g["wall_seconds"]) for g in games), 3),
        "scorecard_score": scorecard_score,
    }
