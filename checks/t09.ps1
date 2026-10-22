$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$k = [string][char]0x65E5 + [char]0x672C
[IO.File]::WriteAllText("$d\lf.cmd", "@echo off`nrem $k$k$k comment`nrem $k more`necho START`necho END`n", [Text.Encoding]::GetEncoding(932))
$o = cmd /c "`"$d\lf.cmd`" 2>&1" | Out-String; $e = $LASTEXITCODE
$extra = @($o -split "`r?`n" | Where-Object { $_.Trim() -ne '' -and $_.Trim() -ne 'START' -and $_.Trim() -ne 'END' })
$o; "console code page $([Console]::OutputEncoding.CodePage), exit=$e, unexpected lines=$($extra.Count)"
if ($e -ne 0 -or $o -notmatch 'START' -or $extra.Count -gt 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
