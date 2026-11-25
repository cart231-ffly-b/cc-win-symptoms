$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\p.txt", "Do exactly these steps and nothing else:`n1. Use the Bash tool with run_in_background set to true to run exactly this command: sleep 123 & timeout 124 sleep 122 & sleep 125 | cat`n2. Use the TaskStop tool to stop that background task.`n3. Reply STOPPED and the task id.")
Push-Location $d
$o = Get-Content "$d\p.txt" -Raw | claude -p --allowedTools "Bash,TaskStop" | Out-String
Pop-Location
Start-Sleep -Seconds 3
$left = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'sleep(\.exe)?"?\s+12[235]\b' })
"claude said: $($o.Trim())"
"processes still running after claude -p ended: $($left.Count)"
$left | ForEach-Object { '  ' + $_.ProcessId + ' ' + $_.CommandLine }
'(leftover sleep processes end by themselves within about two minutes)'
if ($o -notmatch 'STOPPED') { 'CANNOT CHECK (claude did not report STOPPED: check that the Bash and TaskStop tools are available and allowed)' } elseif ($left.Count -gt 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
