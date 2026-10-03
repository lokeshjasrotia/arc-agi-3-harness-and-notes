# 6. Reproducibility checklist

A claim is accepted only if every box can be ticked from the repository alone.

- [ ] A result file in `results/` exists and passes `python -m arcbench.report`.
- [ ] It records the full 40-character git SHA, `dirty: false`, the split and the exact command.
- [ ] The SHA exists in the public history (pushed, not local-only).
- [ ] Python 3.12 and the `arc-agi` version are recorded in the result file.
- [ ] The comparison includes both baselines and at least one public agent, same games/seeds/steps.
- [ ] Seeds are listed; the agent honours them (or the limitation is stated).
- [ ] Per-game numbers are shown, not only the mean.
- [ ] Failures and negative results are in `docs/experiments/`.
- [ ] No claim of a ceiling or impossibility without evidence.

## Reproduce a result

```powershell
git checkout <sha-from-result-file>
.\.venv\Scripts\python.exe <command-from-result-file, prefixed with the interpreter>
```
