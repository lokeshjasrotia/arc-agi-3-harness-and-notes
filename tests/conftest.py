import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GOOD = {
    "schema_version": 1,
    "created_utc": "2026-10-03T10:00:00+00:00",
    "agent": {"name": "RandomBaseline", "path": "baselines/random_agent.py", "file_sha256": "0" * 64},
    "git": {"sha": "a" * 40, "dirty": False, "branch": "main"},
    "split": "public-local",
    "command": "python -m arcbench.runner --agent baselines/random_agent.py",
    "environment": {"python": "3.12.0", "platform": "test", "arc_agi": "0.9.6"},
    "config": {"games": ["ls20"], "seeds": [0], "max_steps": 80, "time_budget_s": None},
    "games": [
        {"game_id": "ls20", "seed": 0, "state": "GameState.NOT_FINISHED",
         "levels_completed": 1, "actions": 80, "wall_seconds": 1.5},
        {"game_id": "vc33", "seed": 0, "state": "GameState.WIN",
         "levels_completed": 3, "actions": 40, "wall_seconds": 0.5},
    ],
    "aggregate": {},
}


@pytest.fixture()
def good():
    return copy.deepcopy(GOOD)
