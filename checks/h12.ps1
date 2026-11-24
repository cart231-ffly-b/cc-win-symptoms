$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
foreach ($v in @('1', '0')) {
  $w = Join-Path $d "v$v"; New-Item -ItemType Directory "$w\sub" -Force | Out-Null
  [IO.File]::WriteAllText("$w\s.json", '{"env":{"CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR":"VAL","CLAUDE_CODE_USE_POWERSHELL_TOOL":"1"}}'.Replace('VAL', $v))
  $p = 'You must use the PowerShell tool (not Bash). Call 1: Set-Location sub . Call 2 (a separate PowerShell tool call): [IO.File]::WriteAllText("OUT", (Get-Location).Path) . Then stop.'.Replace('OUT', "$w\call2.txt")
  Push-Location $w
  $p | claude -p --settings s.json --allowedTools PowerShell | Out-Null
  Pop-Location
}
$r1 = ''; $r0 = ''
if (Test-Path "$d\v1\call2.txt") { $r1 = (Get-Content "$d\v1\call2.txt" -Raw).Trim() }
if (Test-Path "$d\v0\call2.txt") { $r0 = (Get-Content "$d\v0\call2.txt" -Raw).Trim() }
"second PowerShell call after cd sub: MAINTAIN=1 -> $r1 ; MAINTAIN=0 -> $r0"
if ((-not $r0) -or (-not $r1)) { 'CANNOT CHECK (the PowerShell tool did not run: it needs a Claude Code version with the PowerShell tool)' } elseif (-not $r0.EndsWith('sub')) { 'CANNOT CHECK (even with MAINTAIN=0 the cd did not stay)' } elseif (-not $r1.EndsWith('sub')) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
