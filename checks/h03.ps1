$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
foreach ($f in @("$env:USERPROFILE\.claude\settings.json", "$PWD\.claude\settings.json", "$PWD\.claude\settings.local.json")) {
  if (Test-Path -LiteralPath $f) { try { $v = (Get-Content -LiteralPath $f -Raw -Encoding UTF8 | ConvertFrom-Json).disableAllHooks; "your settings: $f -> disableAllHooks=$v" } catch { "your settings: $f -> not valid JSON" } }
}
[IO.File]::WriteAllText("$d\deny.ps1", '[IO.File]::WriteAllText(''MARK'', ''x''); [Console]::Error.WriteLine("denied"); exit 2'.Replace('MARK', "$d\called.txt"))
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -File \"' + ($d -replace '\\', '/') + '/deny.ps1\"'
[IO.File]::WriteAllText("$d\s.json", '{"disableAllHooks":true,"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK","onFailure":"block"}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"; $c = Test-Path "$d\called.txt"
"deny hook with onFailure block, plus disableAllHooks true: hook called=$c, written=$w"
if ((-not $c) -and $w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
