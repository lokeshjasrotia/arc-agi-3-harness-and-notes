# Contributing

Thank you for helping. This project is a research artefact first, so the bar is
**traceability**, not speed.

## Ground rules

1. **No number without a result file.** Any performance claim (README, docs, PR text)
   must point at a committed file in `results/` that records the git SHA, split and exact
   command. `python -m arcbench.report` rejects files that do not.
2. **Never score a candidate only against itself.** Compare against the baselines in
   `baselines/` and against at least one public agent (see `docs/04-benchmark-methodology.md`).
3. **Do not declare ceilings.** Write "not yet reached", with the evidence, instead.
4. **Windows safety.** Any script using multiprocessing needs
   `if __name__ == "__main__": multiprocessing.freeze_support()`, and worker counts are
   hard-coded low (never auto-detected).
5. **Offline compliance.** Nothing in submitted code may need the internet at run time.

## Workflow

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\scripts\dev.ps1 lint
.\scripts\dev.ps1 test
```

* Branch from `main`: `feat/<topic>`, `exp/<id>-<slug>`, `docs/<topic>`.
* Commit messages: `type(scope): summary` (`feat`, `fix`, `exp`, `docs`, `test`, `chore`).
* Open a pull request using the template; CI must be green.

## Recording an experiment

Copy `docs/experiments/TEMPLATE.md` to `docs/experiments/EXP-NNN-slug.md`, fill the
hypothesis **before** running, then link the result file(s). Failed experiments are kept.
