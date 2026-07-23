# Alias: attach LoopLab to Hermes (plugin-style junctions)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& (Join-Path $Root "scripts\install.ps1")
