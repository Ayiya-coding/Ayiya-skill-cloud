param(
  [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex"),
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Get-FullPath([string]$Path) {
  return [System.IO.Path]::GetFullPath($Path)
}

function Invoke-MirrorCopy {
  param(
    [string]$Source,
    [string]$Destination,
    [string]$AllowedRoot
  )

  $sourceFull = Get-FullPath $Source
  $destinationFull = Get-FullPath $Destination
  $allowedFull = Get-FullPath $AllowedRoot

  if (-not (Test-Path -LiteralPath $sourceFull)) {
    throw "Source does not exist: $sourceFull"
  }

  if (-not $destinationFull.StartsWith($allowedFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to write outside Codex home: $destinationFull"
  }

  if (-not (Test-Path -LiteralPath $destinationFull)) {
    New-Item -ItemType Directory -Path $destinationFull | Out-Null
  }

  $args = @($sourceFull, $destinationFull, "/MIR", "/R:2", "/W:1", "/NFL", "/NDL", "/NP")
  if ($DryRun) {
    $args += "/L"
  }

  Write-Host ""
  Write-Host "Syncing:"
  Write-Host "  From: $sourceFull"
  Write-Host "  To:   $destinationFull"
  if ($DryRun) {
    Write-Host "  Mode: dry run, no files will be changed"
  }

  & robocopy @args
  $code = $LASTEXITCODE
  Write-Host "Robocopy exit code: $code"

  if ($code -gt 7) {
    throw "Robocopy failed with exit code $code"
  }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$codexHomeFull = Get-FullPath $CodexHome

if ((Split-Path -Leaf $codexHomeFull) -ne ".codex") {
  throw "CodexHome must point to a .codex directory. Current value: $codexHomeFull"
}

$skillsSource = Join-Path $repoRoot "skills"
$pluginsSource = Join-Path $repoRoot "plugins"
$skillsTarget = Join-Path $codexHomeFull "skills"
$pluginsTarget = Join-Path $codexHomeFull "plugins"

New-Item -ItemType Directory -Force -Path $codexHomeFull | Out-Null
New-Item -ItemType Directory -Force -Path $pluginsTarget | Out-Null

Invoke-MirrorCopy -Source $skillsSource -Destination $skillsTarget -AllowedRoot $codexHomeFull
Invoke-MirrorCopy -Source (Join-Path $pluginsSource "cache") -Destination (Join-Path $pluginsTarget "cache") -AllowedRoot $codexHomeFull
Invoke-MirrorCopy -Source (Join-Path $pluginsSource "cc") -Destination (Join-Path $pluginsTarget "cc") -AllowedRoot $codexHomeFull

Write-Host ""
Write-Host "Done. Restart Codex so it reloads skills and plugins."
