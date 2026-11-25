$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\s.json", '{"env":{"CLAUDE_CODE_USE_POWERSHELL_TOOL":"1"}}')
Push-Location $d
$out = "You must use the PowerShell tool (not Bash). Run exactly the PowerShell command in the next line once, then stop.`ncmd /c exit 3; 'done'" | claude -p --settings s.json --allowedTools PowerShell --output-format stream-json --verbose | Out-String
Pop-Location
$ran = $out -match 'done'
$err = $out -match '"is_error":true'
"the PowerShell tool ran the command: $ran; the call was reported as an error: $err"
if (-not $ran) { 'CANNOT CHECK (the PowerShell tool did not run: check that claude -p can use it)' } elseif ($err -and ($out -match 'Exit code 3')) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
