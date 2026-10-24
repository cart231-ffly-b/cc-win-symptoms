$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$jp = [string][char]0x65E5 + [char]0x672C + [char]0x8A9E
$t = Join-Path $d $jp; New-Item -ItemType Directory $t -Force | Out-Null
$py = & python -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1
if (-not $py) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
[IO.File]::WriteAllText("$d\deny_all.py", "import sys, json`nopen(r'MARK', 'w').close()`ndata = json.load(sys.stdin)`nprint(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': 'deny_all'}}))`n".Replace('MARK', "$d\called.txt"))
$hook = '\"' + ($py -replace '\\', '/') + '\" \"' + ($d -replace '\\', '/') + '/deny_all.py\"'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
[IO.File]::WriteAllText("$d\prompt.md", "Use the Write tool once to create the file $t\written.txt with the content hi. Do not retry if it is blocked.", (New-Object Text.UTF8Encoding $false))
Push-Location $d
"Read the file $d\prompt.md and do exactly what it says." | claude -p --settings s.json --permission-mode acceptEdits --allowedTools "Read,Write" | Out-Null
Pop-Location
$w = Test-Path "$t\written.txt"; $c = Test-Path "$d\called.txt"
"deny-all Python hook, target folder with a Japanese name: hook called=$c, written=$w"
if (-not $c) { 'CANNOT CHECK (the hook was never called: check disableAllHooks or your settings)' } elseif ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
