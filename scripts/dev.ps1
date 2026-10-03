<#
 PowerShell task runner (Windows has no `make`). Run from the repo root:
   .\scripts\dev.ps1 <task>
 Tasks: setup | lint | test | bench | report | token-check
#>
param([Parameter(Position = 0)][string]$Task = "help", [string]$Games = "ls20,vc33", [int]$Steps = 200)

$ErrorActionPreference = "Stop"
$Py = ".\.venv\Scripts\python.exe"

switch ($Task) {
    "setup"  { & $Py -m pip install -r requirements-dev.txt }
    "lint"   { & $Py -m ruff check . }
    "test"   { & $Py -m pytest }
    "bench"  {
        # Baselines first, then your own agent (pass -Agent path -Class name), same games/seeds/steps.
        & $Py -m arcbench.runner --agent baselines\random_agent.py --class RandomBaseline --games $Games --max-steps $Steps --seeds 0,1,2
        & $Py -m arcbench.runner --agent baselines\sweep_agent.py  --class SweepBaseline  --games $Games --max-steps $Steps --seeds 0
    }
    "report" { & $Py -m arcbench.report --update-readme }
    "token-check" {
        $env:KAGGLE_API_TOKEN = (Get-Content .kaggle\access_token -Raw).Trim()
        & .\.venv\Scripts\kaggle.exe competitions list -s arc-prize
    }
    default  { Get-Help $MyInvocation.MyCommand.Path }
}
