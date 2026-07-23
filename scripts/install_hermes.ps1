# Optional: install LoopLab skills into Hermes Agent home (discouraged).
# Prefer keeping LoopLab external. To remove: python -m looplab uninstall-hermes
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m pip install -e . -q
if ($args -notcontains "--yes") {
  Write-Host "Refusing: LoopLab stays outside Hermes. Pass --yes to force install, or run: python -m looplab uninstall-hermes"
  exit 2
}
python -m looplab install-hermes @args
