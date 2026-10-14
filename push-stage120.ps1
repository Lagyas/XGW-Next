$ErrorActionPreference = 'Stop'
$repo = 'F:\XGW-Next'
$zip = Join-Path $PSScriptRoot 'XGW-Next-Stage120.zip'
if (-not (Test-Path $zip)) { throw "Missing archive: $zip" }
if (-not (Test-Path (Join-Path $repo '.git'))) { throw "Not a Git repository: $repo" }
Set-Location $repo
if ((git status --porcelain).Length -gt 0) { throw 'Working tree has uncommitted changes. Commit/stash them first.' }
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Git fetch failed.' }
$localHead = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse origin/main).Trim()
if ($localHead -ne $remoteHead) { throw "Local HEAD $localHead differs from origin/main $remoteHead. Synchronize first." }
$temporary = Join-Path $env:TEMP ('xgw-stage120-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
  Expand-Archive -LiteralPath $zip -DestinationPath $temporary
  $source = Join-Path $temporary 'XGW-Next-Stage120'
  if (-not (Test-Path (Join-Path $source 'editor\app.py'))) { throw 'Unexpected ZIP structure' }
  robocopy $source $repo /E /XD .git __pycache__ .pytest_cache .venv dist build /XF *.pyc | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "Robocopy failed: $LASTEXITCODE" }
  git add -A
  git diff --cached --stat
  if (-not (git diff --cached --quiet)) {
    git commit -m 'Stages 112-120: project safety, MIDI validation, editor sync and Windows beta checks / Bezpecne ukladani, MIDI validace, synchronizace editoru a Windows beta'
    if ($LASTEXITCODE -ne 0) { throw 'Commit failed' }
    git push origin HEAD:main
    if ($LASTEXITCODE -ne 0) { throw 'Push failed' }
  } else {
    Write-Host 'No changes to commit.'
  }
  git status --short
  git log -1 --oneline
} finally {
  Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue
}
