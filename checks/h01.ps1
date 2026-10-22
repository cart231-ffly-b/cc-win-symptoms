$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\slow-deny.ps1", 'Start-Sleep -Seconds 15; [Console]::Error.WriteLine("denied"); exit 2')
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -File ' + ($d -replace '\\', '/') + '/slow-deny.ps1'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK","timeout":3}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"
"hook denies after 15 s, timeout 3 s: written=$w"
if ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
