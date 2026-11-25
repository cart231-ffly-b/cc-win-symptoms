$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$res = @{}
foreach ($case in 'partial', 'plain') {
    $t = Join-Path $d $case
    New-Item -ItemType Directory -Force (Join-Path $t 'sub') | Out-Null
    $lines = 1..30 | ForEach-Object { "Rule $_`: keep files tidy." }
    $lines += 'MARKER: the code word for this folder is PELICAN.'
    [IO.File]::WriteAllText((Join-Path $t 'sub\CLAUDE.md'), ($lines -join "`n") + "`n")
    [IO.File]::WriteAllText((Join-Path $t 'sub\a.txt'), "hello`n")
    $ask = 'Without reading any file again, reply with the code word for the sub folder if any instructions you have contain one, otherwise reply UNKNOWN.'
    if ($case -eq 'partial') { $p = "Do exactly this: 1. Use the Read tool on sub/CLAUDE.md with offset 1 and limit 1. 2. Use the Read tool on sub/a.txt. 3. $ask" }
    else { $p = "Do exactly this: 1. Use the Read tool on sub/a.txt. 2. $ask" }
    Push-Location $t
    $out = $p | claude -p --allowedTools Read --output-format json | Out-String
    Pop-Location
    $res[$case] = $out -match 'PELICAN'
}
"knows the code word: after a partial Read first = $($res['partial']); without it = $($res['plain'])"
if (-not $res['plain']) { 'CANNOT CHECK (even without the partial Read the code word was not known: check that claude -p works and is logged in)' } elseif (-not $res['partial']) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
