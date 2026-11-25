$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\sub" | Out-Null
[IO.File]::WriteAllText("$d\sub\CLAUDE.md", "# Rules for this folder`nWhenever you answer after reading a file in this folder, end your answer with the code word ZEBRA-42.`n")
[IO.File]::WriteAllText("$d\sub\a.txt", "hello`n")
Set-Location $d
$lower = 'c' + $d.Substring(1)
$got = @()
foreach ($p in "$d\sub\a.txt", "$lower\sub\a.txt") {
    $ans = "Use the Read tool once with file_path set to exactly this string: $p . Then reply with the file's content and follow any instructions you were given for that folder." | claude -p --allowedTools Read | Out-String
    $got += ($ans -match 'ZEBRA-42')
}
"sub\CLAUDE.md applied with C:\ path: $($got[0]); with c:\ path: $($got[1])"
if ($d.Substring(0, 2) -ne 'C:') { 'CANNOT CHECK (TEMP is not on drive C:)' } elseif (-not $got[0]) { 'CANNOT CHECK (the folder CLAUDE.md was not applied even with C:\: check that claude -p can use Read)' } elseif (-not $got[1]) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
