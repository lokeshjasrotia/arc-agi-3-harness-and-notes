# 3. Agent architecture (design)

> **Status: design, not yet implemented.** Nothing here is a performance claim. Each component
> becomes real only when an experiment note in `docs/experiments/` and a result file back it.

Notation: grid `H×W = 64×64 = 4096` cells, colours `uint8`; `A` = number of available actions;
`S` = number of distinct states visited; `B` = per-game wall-clock budget.

## 3.1 State representation

* Frame → `np.ndarray[uint8, (64,64)]`. State key = 64-bit hash of `grid.tobytes()`
  (e.g. `hash(bytes)` or `blake2b(digest_size=8)`). **Time O(HW)** per frame, **memory O(1)** per key.
* The state graph stores only `key → {action → (next_key, Δ-summary)}` and parent pointers, never
  full grids (a full grid is ~4 KB; 10⁵ states would be ~400 MB). Keep a bounded LRU of full grids
  only for the states currently needed for diffing. **Memory O(S·A)** small integers.
* Level boundary: `levels_completed` increasing marks a new level; the graph is reset per level
  but the learned *action-effect model* is kept (mechanics usually persist across levels).

## 3.2 Perception: objects and diffs

* Connected-component labelling per colour (4-neighbourhood, NumPy/iterative BFS): **O(HW)** per frame.
* `diff(prev, next)` → changed-cell mask → components → *event list*: `moved(obj, dx, dy)`,
  `recoloured(obj, c1→c2)`, `appeared`, `disappeared`, `blocked` (action issued, nothing changed).
* The agent / player object is hypothesised as the component whose centroid changes most consistently
  with directional actions.

## 3.3 Exploration policy

* Per state, try each untried available action once (**novelty-first**), preferring actions whose
  effect in similar contexts was informative. Never repeat a `(state, action)` pair.
* For the click action, do not sample all 4096 cells: click one cell per *object* and one per
  distinct colour region first (**O(#objects)** instead of O(HW)), then fall back to a coarse lattice
  (see `baselines/sweep_agent.py`).
* Frontier = visited states with untried actions. When the current state has none, plan a shortest
  path to the nearest frontier with BFS: **O(S·A)** time, **O(S)** memory.

## 3.4 Rule induction

Maintain an *action-effect table* keyed by `(action, local context)` → predicted event. A hypothesis
is accepted when it explains **all** observed transitions (consistency check across the interaction
trace), and pruned on the first counter-example. Typical hypothesis families: translation by `(dx,dy)`
with wall collision, colour toggling, push/pull of objects, key/door pairing, counter-based goals.

## 3.5 Planning

* With a predictive model: A\* over simulated states with a heuristic such as Manhattan distance from
  the player object to the nearest goal-coloured component. **Worst case O(b^d)**, bounded by a node
  cap and the time budget; memory capped by the same node cap.
* Without a trustworthy model: stay in frontier exploration (3.3).
* **Goal detection** is itself a hypothesis: states immediately preceding `levels_completed += 1` are
  mined for shared features (colour adjacency, object overlap) to guide later levels.

## 3.6 Budgeting and safety

* Hard per-game wall-clock budget `B`; `arcbench.runner --time-budget` enforces it cooperatively.
* **Fallback policy:** on any exception, stall or budget exhaustion, drop to `SweepBaseline`-style
  actions so a game always returns a valid (if low) score.
* Total budget: `Σ B_game ≤ 9 h` minus a safety margin (target ≤ 7.5 h).
* Offline only: no network, only wheels available on the Kaggle image or in the competition dataset.

## 3.7 What would falsify this design

* The action-effect table cannot explain transitions on most public games → rule induction is the wrong abstraction.
* Frontier exploration spends more actions than the sweep baseline → exploration heuristics are not helping.
* Per-frame cost makes the 9 h budget infeasible → simplify perception.

## Exercises

1. Run `RandomBaseline` and `SweepBaseline` on three games; explain the difference in levels completed.
2. Implement the state hash and a visited-set; measure what fraction of random-agent steps are revisits.
3. Add a `diff` function and print the event list for each action in a game; identify the player object.
4. Implement frontier BFS exploration and compare against the sweep baseline with `arcbench.runner`.
