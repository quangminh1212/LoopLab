# Install LoopLab skills into Hermes Agent home (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m pip install -e . -q
python -m looplab install-hermes @args
