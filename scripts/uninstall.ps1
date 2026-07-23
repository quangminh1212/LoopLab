#Requires -Version 5.1
<#
.SYNOPSIS
  Detach LoopLab external module from local Hermes Agent.
  Only removes junctions (and optional context file). Does not delete this repo.
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hermes = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$SkillsDstRoot = Join-Path $Hermes 'skills'
$SkillsSrc = Join-Path $Root 'skills'

Write-Host "== LoopLab detach ==" -ForegroundColor Cyan
Write-Host "Hermes: $Hermes"

function Remove-JunctionOrWarn($path) {
  if (-not (Test-Path $path)) {
    Write-Host "missing (ok): $path"
    return
  }
  $item = Get-Item $path -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    cmd /c "rmdir `"$path`"" | Out-Null
    Write-Host "removed junction: $path"
  } else {
    throw "Path exists and is not a junction (refusing delete): $path — remove manually if it is a leftover copy."
  }
}

# Known skill package names from this repo
$names = @()
if (Test-Path $SkillsSrc) {
  Get-ChildItem $SkillsSrc -Directory | ForEach-Object {
    if (Test-Path (Join-Path $_.FullName 'SKILL.md')) { $names += $_.Name }
  }
}
if ($names.Count -eq 0) { $names = @('looplab', 'loop-triage', 'loop-engineer') }

foreach ($n in $names) {
  Remove-JunctionOrWarn (Join-Path $SkillsDstRoot $n)
}

# Also clean legacy copied agents/patterns (from older install)
foreach ($rel in @(
  'agents\looplab',
  'looplab-patterns',
  'looplab-HERMES.md',
  'prefill_crew_loop.json'
)) {
  $p = Join-Path $Hermes $rel
  if (-not (Test-Path $p)) { continue }
  $item = Get-Item $p -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    if ($item.PSIsContainer) { cmd /c "rmdir `"$p`"" | Out-Null } else { Remove-Item $p -Force }
    Write-Host "removed link: $p"
  } elseif (-not $item.PSIsContainer) {
    Remove-Item $p -Force
    Write-Host "removed file: $p"
  } elseif ($rel -eq 'agents\looplab' -or $rel -eq 'looplab-patterns') {
    # only remove dirs we own
    Remove-Item -Recurse -Force $p
    Write-Host "removed dir: $p"
  }
}

Write-Host ""
Write-Host "OK. SoT remains at $Root" -ForegroundColor Green
Write-Host "Re-attach: powershell -File $Root\scripts\install.ps1"
Write-Host "Restart Hermes chat/session if skills list is cached."
