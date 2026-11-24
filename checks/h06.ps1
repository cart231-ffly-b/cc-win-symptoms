$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
Set-Content -LiteralPath "$d\app.settings.json" -Value old
$short = (cmd /c dir /x "$d" | Select-String 'app\.settings\.json' | ForEach-Object { ($_.Line -split '\s+') | Where-Object { $_ -match '~[0-9]' } } | Select-Object -First 1)
if (-not $short) { 'CANNOT CHECK (no 8.3 short name on this drive: dir /x shows none, so this cannot happen here)' } else {
"short name: $short"
Push-Location $d
"Use the Write tool once to overwrite the file $short in the current folder with the single line new. Use exactly that file name. Do not use any other tool. Do not retry." | claude -p --permission-mode bypassPermissions | Out-Null
Pop-Location
$long = Test-Path -LiteralPath "$d\app.settings.json"
$names = (Get-ChildItem -LiteralPath $d -Force | ForEach-Object { $_.Name }) -join ', '
"after the write: files = $names"
if ((-not $long) -and ($names -match [regex]::Escape($short))) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
