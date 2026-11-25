$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
New-Item -ItemType Directory -Force "$d\.claude" | Out-Null
$settings = @'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe",
            "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "${CLAUDE_PROJECT_DIR}/.claude/hooks/missing-script.ps1"],
            "onFailure": "block",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
'@
[IO.File]::WriteAllText("$d\.claude\settings.json", $settings)
Push-Location $d
'Use the Write tool once to create out.txt with the text hi. Do not retry. Then reply done.' | claude -p --allowedTools Write | Out-Null
Pop-Location
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$d\.claude\hooks\missing-script.ps1" 2>$null | Out-Null
$code = $LASTEXITCODE
$w = Test-Path "$d\out.txt"
"exit code of powershell -File <missing .ps1>: $code; out.txt written despite onFailure block: $w"
if ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
