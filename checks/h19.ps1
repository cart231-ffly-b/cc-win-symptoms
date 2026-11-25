$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$real = Join-Path $d 'real'
$link = Join-Path $d 'link'
New-Item -ItemType Directory -Force "$real\repo" | Out-Null
cmd /c mklink /J "$link" "$real" | Out-Null
git -C "$real\repo" init -q 2>$null
if (-not (Test-Path "$link\repo")) { 'CANNOT CHECK (could not create the junction with mklink /J)' } else {
Push-Location "$link\repo"
$init = 'reply ok' | claude -p --model haiku --output-format stream-json --verbose --max-turns 1 | Where-Object { $_ -match '"subtype":"init"' } | Select-Object -First 1
Pop-Location
$cwd = [regex]::Match([string]$init, '"cwd":"([^"]+)"').Groups[1].Value.Replace('\\', '\')
"launched in: $link\repo"
"init cwd   : $cwd"
if (-not $cwd) { 'CANNOT CHECK (no init line from claude -p: check that claude -p works and is logged in)' } elseif ($cwd -like '*\real\repo') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
