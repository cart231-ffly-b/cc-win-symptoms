$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\a\b\sub" | Out-Null
[IO.File]::WriteAllText("$d\a\b\sub\SKILL.md", "markerterm`n")
Push-Location $d
$found = @()
foreach ($g in '**/SKILL.md', '*/SKILL.md') {
    $out = "Use the Grep tool exactly once with pattern set to markerterm, path set to exactly $d\a\b , glob set to exactly $g , and output_mode files_with_matches. Use no other tools. Then stop." | claude -p --allowedTools Grep --output-format stream-json --verbose | Out-String
    $found += ($out -match 'Found 1 file')
}
Pop-Location
"glob **/SKILL.md found the file: $($found[0]); glob */SKILL.md found the file: $($found[1])"
if (-not $found[0]) { 'CANNOT CHECK (even **/SKILL.md found nothing: check that claude -p can use Grep)' } elseif (-not $found[1]) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
