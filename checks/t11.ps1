$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory "$d\inc" -Force | Out-Null
[IO.File]::WriteAllText("$d\inc\a.ps1", 'x'); [IO.File]::WriteAllText("$d\inc\b.md", 'x')
$n = @(Get-ChildItem -LiteralPath "$d\inc" -Recurse -File -Include *.ps1).Count
"matched $n files for -Include *.ps1 (expected 1)"
if ($n -eq 2) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
