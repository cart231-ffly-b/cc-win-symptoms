$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$ad = Join-Path $env:LOCALAPPDATA ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $ad -Force | Out-Null
$log = Join-Path $ad 'w.log'; [IO.File]::WriteAllText($log, '')
[IO.File]::WriteAllText("$d\writer.py", "import sys,time`nf=open(sys.argv[1],'a')`nf.write('x'*5000000)`nf.flush()`ntime.sleep(20)`nf.close()`n")
$p = Start-Process python -ArgumentList "`"$d\writer.py`"", "`"$log`"" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5
$listed = (Get-ChildItem -LiteralPath $ad -Filter 'w.log').Length
$fs = [IO.File]::Open($log, 'Open', 'Read', 'ReadWrite'); $real = $fs.Length; $fs.Close()
$p.WaitForExit(); Remove-Item -LiteralPath $ad -Recurse -Force
"listed=$listed real=$real"
if ($listed -ne $real) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
