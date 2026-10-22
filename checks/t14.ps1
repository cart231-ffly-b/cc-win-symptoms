$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$o = claude -p --allowedTools Read 'say hi' 2>&1 | Out-String
($o.Trim() -split "`n")[0]
if ($o -match 'Input must be provided') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
