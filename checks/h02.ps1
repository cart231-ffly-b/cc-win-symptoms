$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\deny.ps1", '[IO.File]::WriteAllText(''MARK'', ''x''); [Console]::Error.WriteLine("denied"); exit 2'.Replace('MARK', "$d\called.txt"))
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -Command \"& ''' + ($d -replace '\\', '/') + '/deny.ps1''\"'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"; $c = Test-Path "$d\called.txt"
"deny hook called through -Command: hook called=$c, written=$w"
if (-not $c) { 'CANNOT CHECK (the hook was never called: check disableAllHooks or your settings)' } elseif ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
