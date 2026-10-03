## What and why

## Evidence
- [ ] Result file(s) committed in `results/` (SHA, split, command recorded) — or N/A (docs/chore)
- [ ] Compared against baselines **and** at least one public agent — or N/A
- [ ] Experiment note added/updated in `docs/experiments/` — or N/A

## Checks
- [ ] `ruff check .` and `pytest` pass
- [ ] No hard-coded worker counts above the documented limit; `freeze_support()` guard present
- [ ] Nothing in submitted code needs internet access
