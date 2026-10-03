# 5. Submission runbook

The push **only validates** the notebook; the click on Kaggle's *Submit to Competition* is what scores it.

This repository does not ship a notebook builder. Our submissions are forks of an open-source notebook
(see [`NOTICE`](../NOTICE)); the steps are done on kaggle.com:

1. Open the source notebook, **Copy & Edit**, and choose the RTX Pro 6000 accelerator by hand.
2. Optional: add `patches/notebook_cell.py` as one extra cell and set `ENABLE_SOLVED_PIN` as wanted.
3. **Save Version** runs the notebook (it uses GPU quota but is *not* a submission).
4. **Submit** / *Submit Prediction* starts a full scored run on the hidden games and uses the daily slot.
5. Use the tick boxes on the Submissions page to pick up to two final submissions.

The Kaggle CLI can list scores: `kaggle competitions submissions arc-prize-2026-arc-agi-3`.

## After every submission

1. Add a row to [`results/LEADERBOARD.md`](../results/LEADERBOARD.md): date, git SHA, agent file hash, public score, notes.
2. Tag the commit: `git tag sub-001 <sha>` and push tags.

## Compliance checklist

* Internet disabled for the notebook; no network calls in submitted code.
* Per-game budget + fallback present (docs/03 §3.6); total expected runtime well under 9 h.
* Accelerator chosen deliberately (RTX Pro 6000 for the Franzen-based notebook).
* Code is open-sourced (prize eligibility).
