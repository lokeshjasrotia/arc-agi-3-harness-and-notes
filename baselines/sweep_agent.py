"""Deterministic systematic-exploration baseline.

Cycles through every simple action, then probes the 64x64 grid with ACTION6
clicks on a coarse lattice (stride ``STRIDE``). It never repeats a click before
the lattice is exhausted. Complexity: O(1) time and memory per decision.

This is the minimum "explore without redundant moves" policy; any learned or
search-based agent must beat it to claim that its exploration is useful.
"""
from __future__ import annotations

from typing import Any

from agents.agent import Agent
from arcengine import FrameData, GameAction, GameState


class SweepBaseline(Agent):
    MAX_ACTIONS = 80
    SEED: int = 0  # unused: fully deterministic; kept for runner compatibility
    STRIDE = 8

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        non_reset = [a for a in GameAction if a is not GameAction.RESET]
        self._simple = [a for a in non_reset if a.is_simple()]
        self._clicks = [
            (x, y)
            for y in range(self.STRIDE // 2, 64, self.STRIDE)
            for x in range(self.STRIDE // 2, 64, self.STRIDE)
        ]
        self._complex = next((a for a in non_reset if a.is_complex()), None)
        self._i = 0

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        n_simple = len(self._simple)
        cycle = n_simple + len(self._clicks) if self._complex else n_simple
        k = self._i % max(cycle, 1)
        self._i += 1
        if k < n_simple:
            action = self._simple[k]
        else:
            action = self._complex
            x, y = self._clicks[k - n_simple]
            action.set_data({"x": x, "y": y})
        action.reasoning = f"systematic sweep step {self._i}"
        return action
