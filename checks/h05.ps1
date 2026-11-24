$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$cmd = (@('@echo off', 'more > nul', 'echo x> "MARK"', 'exit /b 2') -join "`r`n").Replace('MARK', "$d\called.txt")
[IO.File]::WriteAllText("$d\deny.cmd", $cmd + "`r`n")
$fwd = '\"' + ($d -replace '\\', '/') + '/deny.cmd\"'
$back = ($d + '\deny.cmd') -replace '\\', '\\'
foreach ($k in @('fwd', 'back')) {
  $w = Join-Path $d $k; New-Item -ItemType Directory $w -Force | Out-Null
  $hook = if ($k -eq 'fwd') { $fwd } else { $back }
  [IO.File]::WriteAllText("$w\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
  Push-Location $w
  'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
  Pop-Location
  if ($k -eq 'fwd') { $c = Test-Path "$d\called.txt" }
}
$wf = Test-Path "$d\fwd\written.txt"; $wb = Test-Path "$d\back\written.txt"
"same deny.cmd: quoted C:/.../deny.cmd -> hook called=$c, written=$wf; unquoted C:\...\deny.cmd -> written=$wb"
if ((-not $c) -or $wf) { 'CANNOT CHECK (the quoted forward-slash hook did not block: check Git for Windows, disableAllHooks or your settings)' } elseif ($wb) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
