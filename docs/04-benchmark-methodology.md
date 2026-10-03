# 4. Benchmark methodology

Goal: make it impossible to fool ourselves. These rules come from a prior competition post-mortem
in which self-play comparisons misled the team four times.

## 4.1 Rules

1. **Never score a candidate only against itself or its own old versions.** Always include
   (a) `RandomBaseline`, (b) `SweepBaseline`, and (c) at least one *public* agent from
   `vendor/ARC-AGI-3-Agents/agents/templates/` or a public Kaggle notebook.
2. **Provenance.** Every number comes from a committed result file with git SHA, split and exact command.
3. **No declared ceilings.** Report what was measured; do not claim what is "unreachable".
4. **Same conditions.** Compare agents with identical games, seeds, `--max-steps` and `--time-budget`.
5. **Verify before asserting.** Read the live rules page; do not infer from banners or old notes.

## 4.2 Splits

| Split id | Meaning | Use |
|---|---|---|
| `public-local` | Public games run locally through the `arc-agi` engine | Development, ablations |
| `kaggle-public-lb` | Kaggle public leaderboard score | Sanity check; log in `results/LEADERBOARD.md` |
| `kaggle-private` | Final private score | Reported only after the competition ends |

Tuning on `public-local` and reporting it as generalisation is a known risk (see 4.5). Hidden games
are the real test.

## 4.3 Metrics

* **Primary (local):** mean `levels_completed` per run and the engine scorecard score
  (human-normalised efficiency) when the engine reports it.
* **Secondary:** wins, errors, total actions, wall-clock seconds.
* Report **mean over seeds with the per-game table**; with few games and seeds, show the spread
  rather than a single number. Seeded agents honour `Agent.SEED`; agents that seed from the clock
  (the default `MyAgent`) are not exactly reproducible, which the result file's `file_sha256` makes visible.

## 4.4 Protocol

```powershell
.\scripts\dev.ps1 bench -Games ls20,vc33 -Steps 200      # baselines, then MyAgent
.\scripts\dev.ps1 report                                  # regenerates the README table
git add results README.md; git commit -m "exp(EXP-001): ..."
```

Result file name: `<UTC date>_<AgentClass>_<sha7>.json`; schema in `arcbench/schema.py`.
CI runs `python -m arcbench.report`, which fails if any committed result lacks a full SHA, a valid
split, or a command.

## 4.5 Threats to validity

* **Overfitting to public games.** Per-game `if game_id == ...` heuristics (the official starter kit encourages one)
  help locally and may not transfer to hidden games. Track a "game-agnostic" variant separately.
* **Few games, few seeds** → wide confidence intervals; avoid ranking agents on small differences.
* **Local vs Kaggle drift.** Engine versions, hardware and timing differ; log Kaggle scores separately.
* **Dirty-tree runs** are not reproducible from the SHA; they are flagged `*` in the table.
* **Clock-seeded agents** make reruns differ.

## 4.6 Where gains actually came from (prior experience)

Improvements came from *execution engineering* — idle-worker cycling, atomic opening, queue guards —
not from tuning plan/config or copying another agent's shape. Prefer experiments that fix execution
bottlenecks (latency, wasted actions, restarts) before adding model complexity.
