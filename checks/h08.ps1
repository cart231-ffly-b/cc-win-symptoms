$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
Push-Location $d
git init -q 2>$null
git -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty -m init 2>$null
'Reply with the single word OK.' | claude -w e1 -p | Out-Null
$list = git worktree list --porcelain 2>$null | Out-String
Pop-Location
$wt = ([regex]::Matches($list, '(?m)^worktree ')).Count
$lock = $list -match 'locked claude'
"worktrees: $wt; lock line after claude -p ended: $lock"
($list -split "`n") | Where-Object { $_ -match '^locked' }
if ($wt -lt 2) { 'CANNOT CHECK (claude -w did not make a worktree: check that git is installed and claude -w works here)' } elseif ($lock) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
