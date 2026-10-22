<#
  check-paste: feeds each checks\<id>.ps1 to "powershell -Command -" line by line, the closest
  non-interactive stand-in for a reader pasting the snippet into a PowerShell window.
    powershell -NoProfile -ExecutionPolicy Bypass -File .\check-paste.ps1 [-SkipClaude] [-SkipSlow]
  Exit 0 = every snippet still ends with REPRODUCED. ASCII-only file.
#>
param([switch]$SkipClaude, [switch]$SkipSlow)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$oem = [System.Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage
$savedEnc = [Console]::OutputEncoding
[Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding($oem)
$bad = 0
$rows = @()
foreach ($f in (Get-ChildItem -LiteralPath (Join-Path $here 'checks') -Filter '*.ps1' | Sort-Object Name)) {
    $id = $f.BaseName
    if ($SkipClaude -and (@('t14', 'h01', 'h02', 'h03') -contains $id)) { continue }
    if ($SkipSlow -and $id -eq 't13') { continue }
    # a blank line after the snippet ends any multi-line block, as pressing Enter would
    $src = [IO.File]::ReadAllText($f.FullName) + "`r`n`r`n"
    $out = @($src | & powershell.exe -NoProfile -ExecutionPolicy Bypass -Command - 2>$null | ForEach-Object { [string]$_ } | Where-Object { $_.Trim() -ne '' })
    $last = ''
    if ($out.Count -gt 0) { $last = $out[$out.Count - 1].Trim() }
    $rows += [pscustomobject]@{ Id = $id; Result = $last }
    if ($last -ne 'REPRODUCED') { $bad++ }
}
[Console]::OutputEncoding = $savedEnc
$rows | Format-Table -AutoSize | Out-String
if ($bad -eq 0) { 'ALL GOOD' } else { "$bad problem(s)" }
exit $(if ($bad -eq 0) { 0 } else { 1 })
