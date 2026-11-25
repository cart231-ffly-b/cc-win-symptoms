$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\.claude\agents" | Out-Null
[IO.File]::WriteAllText("$d\.claude\agents\ro.md", "---`nname: ro`ndescription: read-only test agent`ntools: Read`n---`nYou answer questions briefly.`n")
$schema = '{\"type\":\"object\",\"properties\":{\"answer\":{\"type\":\"string\"}},\"required\":[\"answer\"]}'
$q = 'What is 2+2? Reply with the answer.'
Push-Location $d
$a = $q | claude -p --model haiku --json-schema $schema --output-format json | Out-String
$b = $q | claude -p --model haiku --json-schema $schema --agent ro --output-format json | Out-String
Pop-Location
$ha = $a -match '"structured_output"'; $hb = $b -match '"structured_output"'; $ok = $b -match '"subtype":"success"'
"without --agent: structured_output=$ha; with --agent ro: structured_output=$hb, subtype success=$ok"
if (-not $ha) { 'CANNOT CHECK (even without --agent there was no structured_output: check that claude -p works and is logged in)' } elseif ((-not $hb) -and $ok) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
