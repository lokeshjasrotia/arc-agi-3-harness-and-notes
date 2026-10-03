# EXP-001 — Fork of Franzen's notebook, then a solved-level pin

* **Status:** in progress   * **Owner:** Lokesh Jasrotia (with Giri)

## Part A: the base (done)
We forked Daniel Franzen's open-source Milestone 2 notebook (Apache-2.0, built on Tufa Labs' Duck
harness) without changing it and submitted it once. Public leaderboard score: **26.02** (about half of the
hidden games). The author's own notebook showed 27.89 on 2026-09-30. A gap of this size is inside the
run-to-run noise other teams report for this kind of notebook (same notebook, three submissions:
5.0 / 5.5 / 6.4 in one public write-up), so it says nothing about any difference between the two.
This is a base-line number, not a result of ours.

## Part B: the solved-level pin (not yet shown to help)
**Hypothesis.** The base trims its chat history from about 118k to about 59k tokens every ~100 actions.
Rules found in early levels can fall out of context. Pinning a short "rule for level N" block at the end of
the system prompt (which is never trimmed) might help on long games. The idea comes from the Milestone 2
write-up by sirikilohit / LohitSiriki, which reported +2.8 at a smaller context size; ours is an independent
implementation (`patches/solved_level_pin.py`, 11 unit tests, off unless `ARC3X_SOLVED_PIN=1`).

**What we measured.** One run on the 10-game public interactive set with the pin on: mean score 33.79. One
earlier run of the unmodified notebook on the same set: 42.76. One run each, so the difference is
dominated by noise and tells us nothing about the pin either way. Trims were confirmed in one game only.

**Open questions.** (1) A control run with the pin off, and at least two runs per arm, compared at equal
generated tokens per game. (2) Whether editing the system prompt costs prefix-cache reuse, once per solved
level (not measured). (3) How often trims happen in the other games.

**Decision rule.** Report the pin as an improvement only if it beats the control by clearly more than the
spread between repeated runs. Otherwise report it as a negative or inconclusive result. Both are kept in
this log.

## Reproduce
Fork the notebook linked in `NOTICE`, add `patches/notebook_cell.py` as one cell, set
`ENABLE_SOLVED_PIN` to True or False, select the RTX Pro 6000 accelerator, and run.
No competition data is stored in this repository.
