$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$hook = @'
import json, sys
from pathlib import Path
d = json.load(sys.stdin)
if d.get("tool_name") != "Bash":
    sys.exit(0)
n = int(Path("n.txt").read_text().strip())
cmd = "printf %s '" + "A" * n + "' > o.txt; echo ok > d.txt"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {"command": cmd}}}))
'@
[IO.File]::WriteAllText("$d\hook.py", $hook)
$hp = ($d + '\hook.py').Replace('\', '/')
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python \"HP\""}]}]}}'.Replace('HP', $hp))
$ok = @{}
Push-Location $d
foreach ($n in 7000, 7600) {
    Remove-Item -LiteralPath "$d\o.txt", "$d\d.txt" -ErrorAction SilentlyContinue
    [IO.File]::WriteAllText("$d\n.txt", "$n")
    'Use the Bash tool once to run: echo hi . Then stop.' | claude -p --settings s.json --allowedTools Bash | Out-Null
    $ok[$n] = (Test-Path "$d\d.txt")
}
Pop-Location
"a 7000-A command ran to the end: $($ok[7000]); a 7600-A command ran to the end: $($ok[7600])"
if (-not $ok[7000]) { 'CANNOT CHECK (even the 7000-character command did not run: check that python is installed and the Bash tool works)' } elseif (-not $ok[7600]) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
