"""Benchmark runner: play an agent on public games and write a result file.

Usage (PowerShell, from the repo root)::

    .\\.venv\\Scripts\\python.exe -m arcbench.runner `
        --agent path\\to\\your_agent.py --class YourAgent `
        --games ls20,vc33 --max-steps 200 --seeds 0,1,2

Design choices
--------------
* Sequential on purpose. No worker pool means no multiprocessing hazards on
  Windows (see project rule 5/6) and results are deterministic for seeded agents.
* A cooperative per-game wall-clock budget (``--time-budget``) stops an agent via
  ``is_done`` so one slow game cannot eat the 9-hour notebook budget.
* Every run emits ``results/<date>_<agent>_<sha7>.json`` containing git SHA,
  dirty flag, split and the exact command, validated by ``arcbench.schema``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import multiprocessing
import platform
import random
import shlex
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .gitinfo import git_info
from .loader import add_framework_to_path, load_agent_class
from .schema import SCHEMA_VERSION, aggregate, validate_result

ROOT = Path(__file__).resolve().parents[1]


def _with_budget(agent_cls: type, seconds: float | None) -> type:
    """Subclass ``agent_cls`` so ``is_done`` also fires when the budget is spent."""
    if not seconds:
        return agent_cls

    class Budgeted(agent_cls):  # type: ignore[misc, valid-type]
        _deadline: float | None = None

        def is_done(self, frames, latest_frame):  # noqa: ANN001
            if self._deadline is None:
                self._deadline = time.monotonic() + seconds
            if time.monotonic() > self._deadline:
                return True
            return super().is_done(frames, latest_frame)

    Budgeted.__name__ = agent_cls.__name__
    return Budgeted


def _resolve_games(all_envs: list[Any], wanted: str | None) -> list[str]:
    short = [e.game_id.split("-")[0] for e in all_envs]
    if not wanted:
        return short
    asked = [g.strip().split("-")[0] for g in wanted.split(",") if g.strip()]
    unknown = sorted(set(asked) - set(short))
    if unknown:
        raise SystemExit(f"Unknown game id(s): {unknown}. Available: {short}")
    return asked


def run(args: argparse.Namespace) -> Path:
    add_framework_to_path(ROOT)
    import arc_agi  # imported late: needs Python 3.12 + the competition wheel
    from arc_agi import OperationMode

    agent_path = Path(args.agent)
    agent_cls = load_agent_class(agent_path, args.agent_class)
    if hasattr(agent_cls, "MAX_ACTIONS"):
        agent_cls.MAX_ACTIONS = min(agent_cls.MAX_ACTIONS, args.max_steps)
    agent_cls = _with_budget(agent_cls, args.time_budget)

    arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
    game_ids = _resolve_games(arc.get_environments(), args.games)
    seeds = [int(s) for s in args.seeds.split(",")]

    rows: list[dict[str, Any]] = []
    for game_id in game_ids:
        for seed in seeds:
            random.seed(seed)
            if hasattr(agent_cls, "SEED"):
                agent_cls.SEED = seed  # seedable agents (baselines) honour this
            row: dict[str, Any] = {
                "game_id": game_id, "seed": seed, "state": "ERROR",
                "levels_completed": 0, "actions": 0, "wall_seconds": 0.0,
            }
            t0 = time.monotonic()
            try:
                env = arc.make(game_id, render_mode=None)
                if env is None:
                    raise RuntimeError(f"arc.make({game_id!r}) returned None")
                agent = agent_cls(
                    card_id="arcbench", game_id=game_id,
                    agent_name=f"arcbench.{args.agent_class}.{game_id}",
                    ROOT_URL="http://localhost", record=False, arc_env=env,
                    tags=["arcbench"],
                )
                agent.main()
                final = agent.frames[-1]
                row.update(state=str(final.state), levels_completed=int(final.levels_completed),
                           actions=int(agent.action_counter))
            except Exception as exc:  # noqa: BLE001 - one bad game must not kill the sweep
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["wall_seconds"] = round(time.monotonic() - t0, 3)
            rows.append(row)
            print(f"{game_id:8} seed={seed:<3} {row['state']:<28} "
                  f"levels={row['levels_completed']:<3} actions={row['actions']:<5} "
                  f"{row['wall_seconds']:.1f}s" + (f"  ERROR {row['error']}" if "error" in row else ""))

    scorecard = arc.get_scorecard()
    score = getattr(scorecard, "score", scorecard)
    score = float(score) if isinstance(score, (int, float)) else None

    git = git_info(ROOT)
    doc = {
        "schema_version": SCHEMA_VERSION,
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "agent": {
            "name": args.agent_class,
            "path": agent_path.as_posix(),
            "file_sha256": hashlib.sha256(agent_path.read_bytes()).hexdigest(),
        },
        "git": git,
        "split": args.split,
        "command": shlex.join(["python", "-m", "arcbench.runner", *sys.argv[1:]]),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "arc_agi": getattr(arc_agi, "__version__", "unknown"),
        },
        "config": {"games": game_ids, "seeds": seeds, "max_steps": args.max_steps,
                   "time_budget_s": args.time_budget},
        "games": rows,
        "aggregate": aggregate(rows, score),
    }
    validate_result(doc)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{doc['created_utc'][:10]}_{args.agent_class}_{str(git['sha'])[:7]}.json"
    out = out_dir / name
    n = 1
    while out.exists():  # never overwrite an earlier result
        n += 1
        out = out_dir / f"{out.stem.split('__')[0]}__{n}.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out}  (dirty tree: {git['dirty']})")
    return out


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--agent", required=True, help="Path to the .py file defining the agent")
    p.add_argument("--class", dest="agent_class", default="MyAgent", help="Agent class name")
    p.add_argument("--games", default=None, help="Comma-separated game ids (default: all)")
    p.add_argument("--max-steps", type=int, default=200)
    p.add_argument("--seeds", default="0", help="Comma-separated integer seeds")
    p.add_argument("--time-budget", type=float, default=None, help="Per-run wall seconds")
    p.add_argument("--split", default="public-local")
    p.add_argument("--out", default=str(ROOT / "results"))
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    run(args)


if __name__ == "__main__":
    multiprocessing.freeze_support()  # required on Windows; harmless elsewhere
    main()
