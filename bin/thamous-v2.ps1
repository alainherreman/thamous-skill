$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path (Split-Path -Parent $ScriptDir) "scripts/thamous_api_v2.py"
python $ScriptPath @args
