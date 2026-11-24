$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory "$d\sub" -Force | Out-Null
$u = $d -replace '\\', '/'
$p = 'Use the Bash tool exactly twice, one command per call. Call 1: cd "U/sub" && pwd > "U/p1.txt" . Call 2: pwd > "U/p2.txt" . Then stop.'.Replace('U', $u)
Push-Location $d
$p | claude -p --allowedTools Bash | Out-Null
Pop-Location
if (-not (Test-Path "$d\p1.txt") -or -not (Test-Path "$d\p2.txt")) { 'CANNOT CHECK (the Bash tool did not run both calls: check that it is available and allowed)' } else {
$p1 = (Get-Content "$d\p1.txt" -Raw).Trim(); $p2 = (Get-Content "$d\p2.txt" -Raw).Trim()
"inside %TEMP%: same call after cd sub -> $p1 ; next call -> $p2"
if (-not $p1.EndsWith('/sub')) { 'CANNOT CHECK (cd did not work even inside the same call)' } elseif (-not $p2.EndsWith('/sub')) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
