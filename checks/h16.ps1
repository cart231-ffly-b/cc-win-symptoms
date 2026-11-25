$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\Sub" | Out-Null
[IO.File]::WriteAllText("$d\Sub\EditBack.txt", "fruit = APPLE`r`n")
Push-Location $d
"First use the Read tool on the file Sub/EditBack.txt in the current folder. Then use the Edit tool exactly once with file_path set to exactly this string, character for character: $d\sub\editback.TXT . Replace APPLE with ORANGE. Use no other tools. Then stop." | claude -p --allowedTools "Read,Edit" | Out-Null
Pop-Location
$name = (Get-ChildItem -LiteralPath "$d\Sub" | ForEach-Object Name) -join ', '
$body = (Get-Content -LiteralPath "$d\Sub\EditBack.txt" -Raw).Trim()
"file name after the Edit: $name; content: $body"
if ($body -notmatch 'ORANGE') { 'CANNOT CHECK (the Edit did not happen: check that claude -p can use Read and Edit)' } elseif ($name -ceq 'editback.TXT') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
