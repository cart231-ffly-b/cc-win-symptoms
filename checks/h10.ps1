$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\p.txt", 'Use the Bash tool once to run exactly this command and nothing else, then stop: printf ''%s'' ''a\\b'' > out.bin')
Push-Location $d
Get-Content "$d\p.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Pop-Location
if (-not (Test-Path "$d\out.bin")) { 'CANNOT CHECK (out.bin was not written: check that the Bash tool is available and allowed)' } else {
$b = [IO.File]::ReadAllBytes("$d\out.bin")
"asked for a, two backslashes, b -> bytes written: " + (($b | ForEach-Object { '{0:x2}' -f $_ }) -join ' ')
if ($b.Length -eq 3) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
