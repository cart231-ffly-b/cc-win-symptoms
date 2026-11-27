# build.py embeds the check scripts, titles and messages in docs/doctor.ps1.
& {
    if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion -lt [version]'5.1' -or
        [Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { return }

    $traps = @'
__TRAPS__
'@ | ConvertFrom-Json
    $messages = @'
__MESSAGES__
'@ | ConvertFrom-Json
    $baseUrl = '__BASE__'
    if ($env:CCDOCTOR_LANG -eq 'ja') {
        $lang = 'ja'
    } elseif ($env:CCDOCTOR_LANG -eq 'en') {
        $lang = 'en'
    } elseif ([Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName -eq 'ja' -or
        [Globalization.CultureInfo]::CurrentCulture.TwoLetterISOLanguageName -eq 'ja') {
        $lang = 'ja'
    } else {
        $lang = 'en'
    }
    $messages = $messages.$lang
    $only = $env:CCDOCTOR_ONLY -split ','

    function Invoke-DoctorCheck($trap, $workDir, $encoding) {
        $process = New-Object System.Diagnostics.Process
        $stdoutReader = $null
        $stderrReader = $null
        try {
            $localAppData = Join-Path $workDir 'LocalAppData'
            $null = [IO.Directory]::CreateDirectory($localAppData)
            $scriptPath = Join-Path $workDir ($trap.id + '.ps1')
            [IO.File]::WriteAllText($scriptPath, $trap.check, [Text.Encoding]::ASCII)

            $start = $process.StartInfo
            $start.FileName = Join-Path $PSHOME 'powershell.exe'
            $start.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $scriptPath + '"'
            $start.WorkingDirectory = $workDir
            $start.UseShellExecute = $false
            $start.RedirectStandardInput = $true
            $start.RedirectStandardOutput = $true
            $start.RedirectStandardError = $true
            $start.StandardOutputEncoding = $encoding
            $start.EnvironmentVariables['TEMP'] = $workDir
            $start.EnvironmentVariables['TMP'] = $workDir
            $start.EnvironmentVariables['LOCALAPPDATA'] = $localAppData

            $null = $process.Start()
            $process.StandardInput.Close()
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $stdoutReader = $process.StandardOutput
            $stderrReader = $process.StandardError
            $stdout = $stdoutReader.ReadToEndAsync()
            $null = $stderrReader.BaseStream.CopyToAsync([IO.Stream]::Null)
            if (-not $process.WaitForExit(60000)) {
                # Windows PowerShell's .NET Process.Kill() only kills the immediate child.
                & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $process.Id /T /F 2>$null | Out-Null
                if (-not $process.HasExited) { $process.Kill() }
                $process.WaitForExit()
                return 'TIMEOUT'
            }
            if (-not $stdout.Wait([Math]::Max(0, 60000 - [int]$watch.ElapsedMilliseconds))) {
                return 'TIMEOUT'
            }

            $last = ($stdout.Result.TrimEnd() -split '\r?\n')[-1].Trim()
            if ($last -match '^(REPRODUCED|NOT REPRODUCED|CANNOT CHECK(?: \(.*\))?)$') { return $last }
            return 'CANNOT CHECK (no check result)'
        } catch {
            return 'CANNOT CHECK (could not run the check)'
        } finally {
            if ($stdoutReader) { $stdoutReader.Dispose() }
            if ($stderrReader) { $stderrReader.Dispose() }
            $process.Dispose()
        }
    }

    $tempRoot = [IO.Path]::GetFullPath($env:TEMP)
    $runDir = Join-Path $tempRoot ('cc-doctor-' + [guid]::NewGuid().ToString('N'))
    $null = [IO.Directory]::CreateDirectory($runDir)
    $savedEncoding = [Console]::OutputEncoding
    $encoding = [Text.Encoding]::GetEncoding((Get-Culture).TextInfo.OEMCodePage)
    $reproduced = 0
    $skippedClaude = 0
    $skippedSlow = $false
    $rows = @(
        try {
            [Console]::OutputEncoding = $encoding
            foreach ($trap in $traps) {
                if ($env:CCDOCTOR_ONLY -and $only -notcontains $trap.id) { continue }
                if ($trap.claude) {
                    $skippedClaude++
                    continue
                }
                if ($trap.slow -and $env:CCDOCTOR_ALL -ne '1') {
                    $skippedSlow = $true
                    continue
                }
                $result = Invoke-DoctorCheck $trap (Join-Path $runDir $trap.id) $encoding
                if ($result -eq 'REPRODUCED') { $reproduced++ }
                $status, $detail = $result -split ' \(', 2
                [pscustomobject]@{
                    Id = $trap.id
                    Status = $status
                    Title = $trap.$lang
                    Detail = $detail
                }
            }
        } finally {
            try { [Console]::OutputEncoding = $savedEncoding } finally { [IO.Directory]::Delete($runDir, $true) }
        }
    )

    $messages.header
    foreach ($row in ($rows | Sort-Object @{ Expression = { $_.Status -ne 'REPRODUCED' } }, Id)) {
        $label = $messages.statuses.($row.Status)
        $line = '{0}  {1}  {2}  |  {3}{4}/{0}.html' -f $row.Id, $label, $row.Title, $baseUrl, $lang
        if ($row.Detail) { $line += '  |  ' + $row.Detail.Substring(0, $row.Detail.Length - 1) }
        $line
    }
    if ($skippedClaude) { $messages.skipped_claude -f $skippedClaude, "$baseUrl$lang/index.html" }
    if ($skippedSlow) { $messages.skipped_slow }
    $messages.summary -f $rows.Count, $reproduced
}
