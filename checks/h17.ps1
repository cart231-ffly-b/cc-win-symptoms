$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$repo = Join-Path $d 'hookrepo'
New-Item -ItemType Directory -Force "$repo\.claude", "$repo\sub\deep" | Out-Null
Push-Location $repo; git init -q 2>$null; Pop-Location
$mark = ($repo + '\hook-ran.txt').Replace('\', '/')
$cmd = 'python -c "open(r''' + $mark + ''',''a'').write(''x'')"'
$settings = @{ hooks = @{ PreToolUse = @(@{ matcher = 'Read'; hooks = @(@{ type = 'command'; command = $cmd }) }) } } | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText("$repo\.claude\settings.json", $settings)
[IO.File]::WriteAllText("$repo\sub\deep\a.txt", "hello`n")
[IO.File]::WriteAllText("$repo\a.txt", "hello`n")
$ran = @{}
foreach ($where in 'root', 'sub\deep') {
    Remove-Item -LiteralPath "$repo\hook-ran.txt" -ErrorAction SilentlyContinue
    Push-Location (Join-Path $repo ($where -replace 'root', ''))
    'Use the Read tool once on a.txt and reply done.' | claude -p --allowedTools Read | Out-Null
    Pop-Location
    $ran[$where] = Test-Path "$repo\hook-ran.txt"
}
"root hook ran when started at the repo root: $($ran['root']); when started in sub\deep: $($ran['sub\deep'])"
if (-not $ran['root']) { 'CANNOT CHECK (the hook did not run even at the root: check that python and git are installed)' } elseif (-not $ran['sub\deep']) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
