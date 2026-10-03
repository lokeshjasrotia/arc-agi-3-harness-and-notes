"""Seedable uniform-random baseline (equivalent in spirit to Stochastic Goose)."""
from __future__ import annotations

import random
from typing import Any

from agents.agent import Agent
from arcengine import FrameData, GameAction, GameState


class RandomBaseline(Agent):
    MAX_ACTIONS = 80
    SEED: int = 0  # set by arcbench.runner

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._rng = random.Random(f"{self.SEED}:{self.game_id}")

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        action = self._rng.choice([a for a in GameAction if a is not GameAction.RESET])
        if action.is_complex():
            action.set_data({"x": self._rng.randint(0, 63), "y": self._rng.randint(0, 63)})
        action.reasoning = f"uniform random: {action.value}"
        return action
