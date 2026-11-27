$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$s = [string][char]0x65E5 + [char]0x672C + [char]0x8A9E
[IO.File]::WriteAllText("$d\note.md", $s, [Text.UTF8Encoding]::new($false))
$a = Get-Content -LiteralPath "$d\note.md"
$b = Get-Content -LiteralPath "$d\note.md" -Encoding UTF8
"default read equals the file: $($a -eq $s); with -Encoding UTF8: $($b -eq $s)"
if ($a -ne $s -and $b -eq $s) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
