# results/

Committed, machine-written result files (`*.json`), one per benchmark run. See
`arcbench/schema.py` for the schema. **Never edit these by hand.** A file lacking a full SHA, a valid
split or a command is rejected by `python -m arcbench.report` (and by CI).

Kaggle-scored submissions are logged by hand in [`LEADERBOARD.md`](LEADERBOARD.md).
