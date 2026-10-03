# 2. Setup on Windows 11 (PowerShell)

`make` is not available on Windows; `scripts/dev.ps1` replaces it.

## Prerequisites

* **Python 3.12 exactly** (`arc-agi` requires it): `winget install Python.Python.3.12`
* git, and a Kaggle account that has **accepted the competition rules**.
* Keep the project **outside** OneDrive/Desktop/Documents — sync corrupts long runs
  (e.g. `C:\Kaggle_Competitions\2026-10_ARC_Prize_2026_AGI_3`).

## Steps

```powershell
cd C:\Kaggle_Competitions\2026-10_ARC_Prize_2026_AGI_3
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
git clone --depth 1 https://github.com/arcprize/ARC-AGI-3-Agents vendor\ARC-AGI-3-Agents
```

## Kaggle token (project-local)

Create a token at kaggle.com → Settings → API → *Create New Token* and save it as a **single line** in
`.kaggle\access_token` (git-ignored). Verify:

```powershell
.\scripts\dev.ps1 token-check     # should list arc-prize-2026-arc-agi-3
```

* `401` → bad/expired token. * `403` on file listing → rules not accepted yet.

## Smoke test

```powershell
.\scripts\dev.ps1 test                       # harness + patch unit tests
```

## Windows pitfalls

* Any multiprocessing script **must** have `if __name__ == "__main__": freeze_support()`.
* Hard-code worker counts low; never auto-detect-and-max.
* Line endings: `.gitattributes` normalises to LF; run `git add --renormalize .` once after adopting it.
