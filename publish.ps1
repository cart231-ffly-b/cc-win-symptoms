# Publish this site to GitHub Pages in one go (run by the owner, not by Claude).
# Creates the public repo, pushes ONLY main (never backup/*), and turns on Pages from main:/docs.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/kosoh/cc-win-symptoms/publish.ps1 [-DryRun]
param([switch]$DryRun)
$ErrorActionPreference = "Continue"  # native stderr + Stop throws in PS 5.1; we check $LASTEXITCODE instead
$repo = "cart231-ffly-b/cc-win-symptoms"
$dir = "C:/Users/kosoh/cc-win-symptoms"
$gh = "C:/Program Files/GitHub CLI/gh.exe"
if (-not (Test-Path $gh)) { $gh = "gh.exe" }

function Step($msg) { Write-Host "== $msg" }

Step "checks"
& $gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "NG: run 'gh auth login' first"; exit 1 }
$branch = (git -C $dir rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "main") { Write-Host "NG: current branch is $branch, expected main"; exit 1 }
$dirty = git -C $dir status --porcelain --untracked-files=no
if ($dirty) { Write-Host "NG: uncommitted changes:"; $dirty; exit 1 }
$emails = git -C $dir log main --format=%ae | Sort-Object -Unique
foreach ($e in $emails) {
  if ($e -notlike "*@users.noreply.github.com") { Write-Host "NG: non-noreply author email in main: $e"; exit 1 }
}
Write-Host "OK: branch main, clean, authors = $($emails -join ', ')"

$hasRemote = (git -C $dir remote) -contains "origin"
if ($DryRun) {
  Write-Host "DRY RUN: would create $repo (public), push main only, enable Pages main:/docs"
  Write-Host "origin already set: $hasRemote"
  exit 0
}

Step "create repo"
& $gh repo view $repo *> $null
if ($LASTEXITCODE -ne 0) {
  & $gh repo create $repo --public --description "Windows symptoms where Claude Code and scripts break silently - one page each (EN/JA)"
  if ($LASTEXITCODE -ne 0) { exit 1 }
} else { Write-Host "repo already exists" }
if (-not $hasRemote) { git -C $dir remote add origin "https://github.com/$repo.git" }

Step "push main only"
git -C $dir push -u origin main
if ($LASTEXITCODE -ne 0) { exit 1 }

Step "enable Pages (main:/docs)"
& $gh api -X POST "repos/$repo/pages" -f "source[branch]=main" -f "source[path]=/docs" *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Pages may already be on; current setting:" }
& $gh api "repos/$repo/pages" --jq ".html_url + \"  status=\" + (.status // \"pending\")"
Write-Host "DONE. First build takes ~1 minute: https://cart231-ffly-b.github.io/cc-win-symptoms/"
