$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\case.txt", "a`tb`tc`n1`t2`t3`n")
Push-Location $d
"Use the Read tool on case.txt, then use the Edit tool once on case.txt with old_string set to exactly one TAB character, new_string set to exactly two space characters, and replace_all true. Use no other tools. Then stop." | claude -p --allowedTools "Read,Edit" | Out-Null
Pop-Location
$b = [IO.File]::ReadAllBytes("$d\case.txt")
"case.txt was 12 bytes with 4 tabs; asked to turn each tab into two spaces; now $($b.Length) bytes, tabs left: $(@($b | Where-Object { $_ -eq 9 }).Count)"
if ($b.Length -eq 12) { 'CANNOT CHECK (the Edit did not happen: check that claude -p can use Read and Edit)' } elseif ($b.Length -eq 8) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
