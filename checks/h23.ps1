$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\.claude\hooks" | Out-Null
Push-Location $d; git init -q 2>$null; Pop-Location
$sh = @'
f=$(python -c "import sys,json; print(json.load(sys.stdin)['tool_input'].get('file_path',''))")
printf 'PWD=%s\nfile_path=%s\n' "$PWD" "$f" > seen.txt
case "$f" in "$PWD"/*) exit 0;; *) echo "BLOCKED: file outside the project" >&2; exit 2;; esac
'@
[IO.File]::WriteAllText("$d\.claude\hooks\guard.sh", $sh.Replace("`r`n", "`n"))
[IO.File]::WriteAllText("$d\.claude\settings.json", '{"hooks":{"PreToolUse":[{"matcher":"Write","hooks":[{"type":"command","command":"bash .claude/hooks/guard.sh"}]}]}}')
Push-Location $d
'Use the Write tool once to create out.txt in the current folder with the text hi. Do not retry. Then reply done.' | claude -p --allowedTools Write | Out-Null
Pop-Location
if (Test-Path "$d\seen.txt") { Get-Content "$d\seen.txt" }
$w = Test-Path "$d\out.txt"
"write inside the project went through: $w"
if (-not (Test-Path "$d\seen.txt")) { 'CANNOT CHECK (the hook did not run: check that python, git and Git for Windows bash are installed)' } elseif (-not $w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
