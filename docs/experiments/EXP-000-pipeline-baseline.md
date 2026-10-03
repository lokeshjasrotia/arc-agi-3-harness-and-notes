# EXP-000 — Pipeline + baseline reference

* **Status:** planned   * **Owner:** Lokesh Jasrotia

## Hypothesis
Not a performance hypothesis. Purpose: prove the toolchain end to end and fix a reference point
that later experiments must beat.

## Setup (to run)
```powershell
.\scripts\dev.ps1 bench -Games ls20,vc33 -Steps 200
```
Agents: `RandomBaseline` (seeds 0,1,2), `SweepBaseline`, `MyAgent` (= unmodified starter).
At least one public agent from `vendor/ARC-AGI-3-Agents/agents/templates/` should be added with the same settings.

## Result
_Pending — no result file committed yet. Do not fill in numbers by hand._

## Decision
If the harness produces valid result files for all agents and one Kaggle submission of the unmodified
starter is logged in `results/LEADERBOARD.md`, close this experiment and start EXP-001.
