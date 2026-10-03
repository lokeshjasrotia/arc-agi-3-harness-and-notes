# 1. Competition and scoring

Source of truth: <https://docs.arcprize.org/arc-prize-2026> and the Kaggle competition pages.
This page summarises them; **verify against the live rules before relying on any detail**
(project rule: read the actual rules page, never infer from a banner).

## Task

ARC-AGI-3 is a Kaggle *code competition* of hidden, interactive grid-based games. The agent
explores, infers the transition dynamics and reaches a goal state. There are no static
input/output pairs to learn from; knowledge must be acquired by acting.

## Scoring

* Per game: 0–100 %, where 100 % means completing it in no more actions than a human
  (efficiency-normalised).
* Overall: the mean across games.
* Consequence: *wasted actions cost score*, so exploration efficiency matters as much as success.

## Runtime constraints

| Constraint | Value |
|---|---|
| Internet | Off |
| Wall-clock | ≤ 9 h total for all hidden games |
| Hardware | CPU, or GPU including RTX 6000 (`g4-standard-48`) |
| Dependencies | Pre-installed packages or offline wheel bundles only |
| Daily submissions | Limited (see the competition page) |

## Dates (2026)

Entry deadline 26 Oct · final submission 2 Nov · winners 4 Dec. Milestones on 30 Jun and 30 Sep have passed.

## Environment API in one paragraph

An agent subclasses `agents.agent.Agent` and implements `is_done(frames, latest_frame)` and
`choose_action(frames, latest_frame) -> GameAction`. Frames expose the game `state`
(`NOT_PLAYED`, `NOT_FINISHED`, `WIN`, `GAME_OVER`), `levels_completed` and the 64×64 grid.
`GameAction.RESET` restarts a level; simple actions take no arguments; the complex action
(`ACTION6`) takes `(x, y)` on the grid.
