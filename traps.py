# The one source for every page. build.py turns this into docs/ (ja + en) and checks/*.ps1.
# Each "check" is a PowerShell 5.1 snippet a reader pastes as is. It must be ASCII-only and
# end by printing REPRODUCED or NOT REPRODUCED. check.ps1 runs every snippet with -File.

AUTHOR_ENV = {
    "ja": "作者の PC: Windows 11 / Windows PowerShell 5.1.26100 / Python 3.13.7 / Claude Code 2.1.304、日本語の Windows（コードページ 932）。2026-10-20〜22 に確認。",
    "en": "Author's machine: Windows 11 / Windows PowerShell 5.1.26100 / Python 3.13.7 / Claude Code 2.1.304, Japanese Windows (code page 932). Checked 2026-10-20 to 22.",
}

HEAD = r"""$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
"""

YES = r"""{ 'REPRODUCED' } else { 'NOT REPRODUCED' }"""

PY_GUARD = r"""$pyv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
if (-not $pyv) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
"python $pyv"
"""
PY_IDS = ("t04", "t05", "t06", "t07", "t13")

TRAPS = [
    {
        "id": "t01",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\exit2.ps1", 'exit 2')
powershell -NoProfile -ExecutionPolicy Bypass -File "$d\exit2.ps1"; $a = $LASTEXITCODE
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '$d\exit2.ps1'"; $b = $LASTEXITCODE
"-File=$a  -Command=$b"
if ($a -eq 2 -and $b -eq 1) """ + YES,
        "ja": {
            "title": "PowerShell の終了コードが、2 を返したのに 1 になる",
            "search": ["PowerShell 終了コード 1 になる", "exit 2 が 1", "タスクスケジューラ 0x1", "powershell -Command 終了コード"],
            "symptom": "スクリプトの中で exit 2 と書いたのに、呼んだ側には 1 が返る。0 と 1 はそのまま返るので、「対象外は 2、失敗は 1」のように分けた判定だけが、黙って崩れる。",
            "why": "powershell -Command \"& 'x.ps1'\" の形で呼ぶと、PowerShell はスクリプトの終了コードではなく「最後のコマンドが成功したか」を 0 か 1 で返す。-File で呼べば、スクリプトの終了コードがそのまま返る。",
            "fix": "スクリプトは -File で呼ぶ。どうしても -Command で呼ぶなら、末尾に ; exit $LASTEXITCODE を付ける。",
            "fixcode": "powershell -NoProfile -ExecutionPolicy Bypass -File .\\x.ps1\npowershell -NoProfile -Command \"& '.\\x.ps1'; exit $LASTEXITCODE\"",
            "result": "-File=2  -Command=1",
        },
        "en": {
            "title": "PowerShell returns exit code 1 when the script exited with 2",
            "search": ["powershell exit code always 1", "powershell -Command exit code wrong", "Task Scheduler last run result 0x1", "powershell script returns exit code 1 instead of 2"],
            "symptom": "The script exits with code 2, but the caller sees 1. Codes 0 and 1 come through unchanged, so only a scheme like \"2 = skipped, 1 = failed\" breaks, and it breaks silently.",
            "why": "When you call powershell -Command \"& 'x.ps1'\", PowerShell returns whether the last command succeeded (0 or 1), not the script's exit code. With -File the script's exit code is returned as is.",
            "fix": "Call scripts with -File. If you must use -Command, end it with ; exit $LASTEXITCODE.",
            "fixcode": "powershell -NoProfile -ExecutionPolicy Bypass -File .\\x.ps1\npowershell -NoProfile -Command \"& '.\\x.ps1'; exit $LASTEXITCODE\"",
            "result": "-File=2  -Command=1",
        },
    },
    {
        "id": "t02",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\arr.ps1", 'param([string[]]$Path) "count=$($Path.Count) first=$($Path[0])"')
$o = powershell -NoProfile -ExecutionPolicy Bypass -File "$d\arr.ps1" -Path a b; $e = $LASTEXITCODE
"$o  exit=$e"
if ($o -eq 'count=1 first=a' -and $e -eq 0) """ + YES,
        "ja": {
            "title": "PowerShell の -File で渡した2つ目の引数が、エラーなしで消える",
            "search": ["powershell -File 配列 引数 渡せない", "string[] 引数 1つしか入らない", "powershell 引数 消える"],
            "symptom": "[string[]] の引数に -Path a b と2つ渡したのに、スクリプトには a しか入っていない。エラーも出ず、終了コードも 0。",
            "why": "-File で呼ぶと、引数は文字列のまま1つずつ渡る。-Path に入るのは a だけで、b はどの引数にも当たらない余りとして $args に回り、そのまま捨てられる。",
            "fix": "param の前に [CmdletBinding()] を付ける。余った引数があるとエラーで止まるようになる。複数の値は1つの文字列で受けて、自分で分ける（次の T03）。",
            "fixcode": "[CmdletBinding()]\nparam([string]$Path)\n$paths = $Path -split ','",
            "result": "count=1 first=a、終了コード 0（[CmdletBinding()] を付けると終了コード 1 で止まった）",
        },
        "en": {
            "title": "The second value passed with PowerShell -File disappears without an error",
            "search": ["powershell -File array parameter only first value", "string[] parameter one element", "powershell -File multiple arguments ignored"],
            "symptom": "You pass -Path a b to a [string[]] parameter, but the script only gets a. No error, exit code 0.",
            "why": "With -File, arguments arrive as plain strings. -Path takes a; b matches no parameter, goes into $args and is dropped.",
            "fix": "Add [CmdletBinding()] before param so an extra argument stops the script with an error. Take several values as one string and split it yourself (see T03).",
            "fixcode": "[CmdletBinding()]\nparam([string]$Path)\n$paths = $Path -split ','",
            "result": "count=1 first=a, exit 0 (with [CmdletBinding()]: stopped with exit 1)",
        },
    },
    {
        "id": "t03",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\arr.ps1", 'param([string[]]$Path) "count=$($Path.Count) first=$($Path[0])"')
$o = powershell -NoProfile -ExecutionPolicy Bypass -File "$d\arr.ps1" -Path a,b
$o
if ($o -eq 'count=1 first=a,b') """ + YES,
        "ja": {
            "title": "PowerShell の -File で a,b と渡すと、配列にならず1つの文字列になる",
            "search": ["powershell -File カンマ 配列にならない", "a,b 1つのパス", "指定されたパスが見つかりません カンマ"],
            "symptom": "-Path a,b と書けば2つのパスになるつもりが、a,b という名前のパス1つとして扱われ、「見つからない」になるか、黙って何もしない。",
            "why": "-File で渡した引数は PowerShell の式として解釈されない。カンマで配列を作るのは、PowerShell の中で呼んだときだけ。",
            "fix": "1つの文字列で受けて、スクリプトの中で -split ',' で分ける。",
            "fixcode": "param([string]$Path)\nforeach ($p in ($Path -split ',')) { $p.Trim() }",
            "result": "count=1 first=a,b",
        },
        "en": {
            "title": "With PowerShell -File, a,b stays one string instead of an array",
            "search": ["powershell -File comma separated array", "powershell -File comma separated argument array", "cannot find path with comma"],
            "symptom": "You write -Path a,b expecting two paths. The script gets one path named a,b, then reports it missing or silently does nothing.",
            "why": "Arguments given with -File are not parsed as PowerShell expressions. The comma makes an array only when you call the script from inside PowerShell.",
            "fix": "Take one string and split it in the script with -split ','.",
            "fixcode": "param([string]$Path)\nforeach ($p in ($Path -split ',')) { $p.Trim() }",
            "result": "count=1 first=a,b",
        },
    },
    {
        "id": "t04",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\hex.py", 'import sys; print(sys.stdin.buffer.read().strip().hex())')
$s = [string][char]0x65E5 + [char]0x672C
$h = $s | python "$d\hex.py"
"bytes=$h  (UTF-8 would be e697a5e69cac)"
if ($h -match '^(efbbbf)?(3f)+$') """ + YES,
        "ja": {
            "title": "PowerShell のパイプで渡した日本語が ? になる（claude -p・python・git）",
            "search": ["PowerShell パイプ 日本語 ?になる", "claude -p 日本語 文字化け", "python stdin 日本語 ??", "$OutputEncoding"],
            "symptom": "PowerShell から \"日本語\" | claude -p のように渡すと、相手には ?? が届く。エラーは出ない。Claude なら「文字化けしていたので推測した」と言いながら、指示と違うことをする。",
            "why": "Windows PowerShell 5.1 は、ネイティブのプログラムへパイプで渡す文字を $OutputEncoding で符号化する。既定は ASCII なので、日本語は ? になる。受け取る側の [Console]::OutputEncoding とは別の設定。",
            "fix": "長い日本語は UTF-8 のファイルに書き、ASCII だけの指示で「このファイルを読んで」と渡す。保険として $OutputEncoding を UTF-8 にする。",
            "fixcode": "$OutputEncoding = New-Object System.Text.UTF8Encoding $false\n'Read C:/work/prompt.md and do exactly what it says.' | claude -p",
            "result": "バイト 3f3f（? が2つ）",
        },
        "en": {
            "title": "Non-ASCII text piped through PowerShell to claude -p, python or git arrives as ?",
            "search": ["powershell pipe unicode question marks", "claude -p non-ascii prompt garbled", "powershell pipe unicode to python question marks", "$OutputEncoding ascii"],
            "symptom": "You pipe text with accents, CJK or emoji into claude -p (or python, git) and the program receives ?. No error. Claude may say the prompt looked garbled and guess.",
            "why": "Windows PowerShell 5.1 encodes text piped into native programs with $OutputEncoding, which defaults to ASCII. Anything outside ASCII becomes ?. It is a different setting from [Console]::OutputEncoding, which only affects reading output.",
            "fix": "Put long non-ASCII text in a UTF-8 file and pipe an ASCII-only instruction to read it. Also set $OutputEncoding to UTF-8.",
            "fixcode": "$OutputEncoding = New-Object System.Text.UTF8Encoding $false\n'Read C:/work/prompt.md and do exactly what it says.' | claude -p",
            "result": "bytes 3f3f (two question marks)",
        },
    },
    {
        "id": "t05",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\say.py", 'import sys; sys.stdout.buffer.write((chr(0x65e5)+chr(0x672c)).encode("utf-8"))')
$s = python "$d\say.py"
$want = [string][char]0x65E5 + [char]0x672C
"read with code page $([Console]::OutputEncoding.CodePage): " + (($s.ToCharArray() | ForEach-Object { '{0:X4}' -f [int]$_ }) -join ' ') + '  (want 65E5 672C)'
if ($s -ne $want) """ + YES,
        "ja": {
            "title": "PowerShell で python や claude の出力を変数に入れると文字化けする",
            "search": ["PowerShell 出力 文字化け 変数", "譌･譛ｬ", "python 出力 文字化け PowerShell", "Console OutputEncoding"],
            "symptom": "画面に直接出すと読めるのに、$x = python ... で受け取ると「譌･譛ｬ」のような文字になる。ログに書くと、そのまま化けて残る。",
            "why": "PowerShell はネイティブのプログラムの出力を [Console]::OutputEncoding（日本語の Windows では既定 932）で読む。相手が UTF-8 で書いていると、読み違える。",
            "fix": "出力を読む側で [Console]::OutputEncoding を UTF-8 にする。送る側の Python は PYTHONIOENCODING を utf-8 に（次の T06）。両方そろえる。",
            "fixcode": "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n$env:PYTHONIOENCODING = 'utf-8'",
            "result": "2文字が別の4文字になった",
        },
        "en": {
            "title": "Output from python or claude turns into mojibake in a PowerShell variable",
            "search": ["powershell native command output encoding wrong", "powershell capture utf-8 output mojibake", "[Console]::OutputEncoding utf8"],
            "symptom": "Printed straight to the screen it looks fine, but $x = python ... holds garbled characters, and so does the log you write from it.",
            "why": "PowerShell decodes a native program's output with [Console]::OutputEncoding, which defaults to the OEM code page (437, 850, 932 ...). Output from a program that writes UTF-8 is decoded incorrectly.",
            "fix": "Set [Console]::OutputEncoding to UTF-8 on the reading side, and PYTHONIOENCODING=utf-8 on the Python side (T06). Do both.",
            "fixcode": "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n$env:PYTHONIOENCODING = 'utf-8'",
            "result": "two characters became four others",
        },
    },
    {
        "id": "t06",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\dash.py", 'print("a" + chr(0x2014) + chr(0x2713) + "b")')
python "$d\dash.py" > "$d\out.txt" 2> "$d\err.txt"; $e = $LASTEXITCODE
$err = [IO.File]::ReadAllText("$d\err.txt")
"exit=$e, UnicodeEncodeError=$($err -match 'UnicodeEncodeError')"
if ($e -ne 0 -and $err -match 'UnicodeEncodeError') """ + YES,
        "ja": {
            "title": "手で動かすと通る Python が、タスクスケジューラやリダイレクトのときだけ UnicodeEncodeError（cp932）で落ちる",
            "search": ["UnicodeEncodeError cp932", "タスクスケジューラ python 動かない", "python リダイレクト エラー", "'cp932' codec can't encode character"],
            "symptom": "画面で動かすと通るスクリプトが、> ファイル へのリダイレクトやタスクスケジューラ経由のときだけ UnicodeEncodeError で落ちる。— や ✓ のような記号を print しただけで起きる。",
            "why": "Windows の Python は、出力先が画面なら Unicode をそのまま書けるが、ファイルやパイプだと既定のコードページ（日本語なら cp932）で符号化する。その表に無い文字で落ちる。なお Python 3.15（2026年10月9日公開）は UTF-8 を既定にしたので（PEP 686）、3.15 以降では起きない見込み（作者の PC は 3.13.7 で、3.15 では試していない。確かめるコードは最初に Python の版を出す）。",
            "fix": "送る側で PYTHONIOENCODING=utf-8 を設定する。アプリで直すなら、画面でないときだけ sys.stdout.reconfigure(encoding='utf-8')。",
            "fixcode": "$env:PYTHONIOENCODING = 'utf-8'",
            "result": "UnicodeEncodeError、終了コード 1",
        },
        "en": {
            "title": "Python works by hand but crashes with UnicodeEncodeError (cp932) under Task Scheduler or redirection",
            "search": ["UnicodeEncodeError charmap codec can't encode character", "python works manually fails in task scheduler", "python redirect output unicode error windows"],
            "symptom": "A script that runs fine in a terminal crashes with UnicodeEncodeError when its output is redirected to a file or it runs from Task Scheduler. Printing a check mark (U+2713) is enough.",
            "why": "On Windows, Python writes Unicode directly to a console, but encodes with the ANSI code page (1252, 932 ...) when output goes to a file or pipe. Characters outside that code page crash it. Python 3.15 (released 2026-10-09) made UTF-8 the default (PEP 686), so this is not expected on 3.15 or later (the author tested 3.13.7, not 3.15; the check prints your Python version first).",
            "fix": "Set PYTHONIOENCODING=utf-8 on the sending side. In the app itself, call sys.stdout.reconfigure(encoding='utf-8') when stdout is not a terminal.",
            "fixcode": "$env:PYTHONIOENCODING = 'utf-8'",
            "result": "UnicodeEncodeError, exit 1",
        },
    },
    {
        "id": "t07",
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\dash.py", 'print("a" + chr(0x2014) + chr(0x2713) + "b")')
$old = $env:PYTHONIOENCODING; $env:PYTHONIOENCODING = 'utf-8'
python -I "$d\dash.py" > "$d\o1.txt" 2> "$d\e1.txt"; $a = $LASTEXITCODE
python "$d\dash.py" > "$d\o2.txt" 2> "$d\e2.txt"; $b = $LASTEXITCODE
$env:PYTHONIOENCODING = $old
$err = [IO.File]::ReadAllText("$d\e1.txt")
"with -I exit=$a, without -I exit=$b"
if ($a -ne 0 -and $err -match 'UnicodeEncodeError' -and $b -eq 0) """ + YES,
        "ja": {
            "title": "PYTHONIOENCODING を設定したのに、python -I だと効かない",
            "search": ["PYTHONIOENCODING 効かない", "python -I 環境変数 無視", "python -I UnicodeEncodeError"],
            "symptom": "T06 の対策で PYTHONIOENCODING=utf-8 を入れたのに、python -I で呼んでいる所だけ同じエラーで落ちる。",
            "why": "-I（隔離モード）は PYTHON で始まる環境変数をすべて無視する。安全のために付けた -I が、文字コードの設定まで消す。Python 3.15 以降は UTF-8 が既定なので、そもそも落ちない見込み（未確認）。",
            "fix": "-I を外すか、スクリプトの中で sys.stdout.reconfigure(encoding='utf-8') を呼ぶ。",
            "fixcode": "import sys\nsys.stdout.reconfigure(encoding='utf-8')",
            "result": "-I で終了コード 1、外すと 0",
        },
        "en": {
            "title": "PYTHONIOENCODING is set, but python -I ignores it",
            "search": ["PYTHONIOENCODING not working", "python -I ignores environment variables", "python -I UnicodeEncodeError"],
            "symptom": "You set PYTHONIOENCODING=utf-8 to fix T06, but the places that call python -I still crash the same way.",
            "why": "-I (isolated mode) ignores every PYTHON* environment variable. The flag you added for safety also drops the encoding setting. On Python 3.15 or later UTF-8 is the default, so this is not expected there (not tested).",
            "fix": "Drop -I, or call sys.stdout.reconfigure(encoding='utf-8') inside the script.",
            "fixcode": "import sys\nsys.stdout.reconfigure(encoding='utf-8')",
            "result": "exit 1 with -I, 0 without",
        },
    },
    {
        "id": "t08",
        "check": HEAD + r"""$want = [string][char]0x65E5 + [char]0x672C
[IO.File]::WriteAllText("$d\nobom.ps1", "Write-Output '$want'", (New-Object System.Text.UTF8Encoding $false))
$o = powershell -NoProfile -ExecutionPolicy Bypass -File "$d\nobom.ps1"
"got $o (want $want)"
if ($o -ne $want) """ + YES,
        "ja": {
            "title": "PowerShell 5.1 で日本語入りの .ps1（BOM なし UTF-8）が、構文エラーになるか文字化けして動く",
            "search": ["ps1 日本語 文字化け", "ps1 BOM 必要", "PowerShell 5.1 UTF-8 構文エラー", "式またはステートメントのトークン"],
            "symptom": "エディタでは正しく見える .ps1 が、実行すると「文字列に終端記号がありません」などの構文エラーになるか、エラーなしで化けた文字を出す。",
            "why": "Windows PowerShell 5.1 は、BOM の無い .ps1 を UTF-8 ではなく ANSI コードページ（日本語なら 932）として読む。今のエディタの多くは BOM なしの UTF-8 で保存する。",
            "fix": "日本語を含む .ps1 は UTF-8（BOM 付き）で保存する。または .ps1 を ASCII だけで書き、日本語は [char]0x65E5 のように組み立てる。",
            "fixcode": "$t = [IO.File]::ReadAllText($path)\n[IO.File]::WriteAllText($path, $t, (New-Object System.Text.UTF8Encoding $true))",
            "result": "出力が元と違った",
        },
        "en": {
            "title": "A UTF-8 .ps1 with non-ASCII text and no BOM fails to parse or prints mojibake in PowerShell 5.1",
            "search": ["powershell 5.1 utf-8 without bom", "ps1 encoding problem accented characters", "the string is missing the terminator utf-8"],
            "symptom": "A .ps1 that looks right in your editor fails with a parse error such as \"The string is missing the terminator\", or runs and prints garbled text.",
            "why": "Windows PowerShell 5.1 reads a .ps1 without a BOM using the ANSI code page, not UTF-8. Most editors now save UTF-8 without a BOM.",
            "fix": "Save .ps1 files that contain non-ASCII text as UTF-8 with BOM, or keep scripts ASCII-only and build characters with [char]0x00E9.",
            "fixcode": "$t = [IO.File]::ReadAllText($path)\n[IO.File]::WriteAllText($path, $t, (New-Object System.Text.UTF8Encoding $true))",
            "result": "output differed from the source (Japanese Windows)",
        },
    },
    {
        "id": "t09",
        "check": HEAD + r"""$k = [string][char]0x65E5 + [char]0x672C
[IO.File]::WriteAllText("$d\lf.cmd", "@echo off`nrem $k$k$k comment`nrem $k more`necho START`necho END`n", [Text.Encoding]::GetEncoding(932))
$o = cmd /c "`"$d\lf.cmd`" 2>&1" | Out-String; $e = $LASTEXITCODE
$extra = @($o -split "`r?`n" | Where-Object { $_.Trim() -ne '' -and $_.Trim() -ne 'START' -and $_.Trim() -ne 'END' })
$o; "console code page $([Console]::OutputEncoding.CodePage), exit=$e, unexpected lines=$($extra.Count)"
if ($e -ne 0 -or $o -notmatch 'START' -or $extra.Count -gt 0) """ + YES,
        "ja": {
            "title": ".cmd / .bat のコメントが、コマンドとして実行される",
            "search": ["bat rem 実行される", "bat 日本語 コメント エラー", "は、内部コマンドまたは外部コマンド rem", "bat 改行コード LF"],
            "symptom": "rem で書いた日本語のコメントの一部が「内部コマンドまたは外部コマンド…として認識されていません」になる。途中の行が飛ばされることもある。文字コードを直しても直らない。",
            "why": "本当の原因は改行。LF だけの .cmd を、cmd.exe がコードページ 932 で読むと、行の区切りを誤ってコメントの途中からを1行として実行する。コードページを 65001（UTF-8）にした端末や Claude Code の Bash ツールの中では起きないので、そこで試すと気づけない。",
            "fix": ".cmd / .bat は改行を CRLF にして保存する。git なら .gitattributes に *.cmd text eol=crlf。",
            "fixcode": "$enc = [Text.Encoding]::GetEncoding(28591)   # 1文字=1バイトで読み書きし、中身のバイトを変えない\n$t = [IO.File]::ReadAllText($path, $enc)\n$t = ($t -replace \"`r`n\", \"`n\") -replace \"`n\", \"`r`n\"\n[IO.File]::WriteAllText($path, $t, $enc)",
            "result": "cp932 で壊れ、cp65001 では通った",
        },
        "en": {
            "title": "A .cmd / .bat file runs its comment text as commands",
            "search": ["batch file rem line executed", "bat file LF line endings", "is not recognized as an internal or external command rem", "cmd LF only line endings"],
            "symptom": "Parts of rem comments come back as \"is not recognized as an internal or external command\", or lines are skipped. Changing the encoding does not fix it.",
            "why": "The real cause is the line endings. cmd.exe can misread line boundaries in an LF-only batch file. On the author's machine it broke under code page 932 (Japanese), not under 65001, 437 or 1252, so on English Windows this check may say NOT REPRODUCED.",
            "fix": "Save .cmd / .bat files with CRLF line endings. In git, add *.cmd text eol=crlf to .gitattributes.",
            "fixcode": "$enc = [Text.Encoding]::GetEncoding(28591)   # one byte per char: the file's bytes stay as they are\n$t = [IO.File]::ReadAllText($path, $enc)\n$t = ($t -replace \"`r`n\", \"`n\") -replace \"`n\", \"`r`n\"\n[IO.File]::WriteAllText($path, $t, $enc)",
            "result": "broke under cp932, ran fine under cp65001",
        },
    },
    {
        "id": "t10",
        "check": HEAD + r"""powershell -NoProfile -Command "foreach ($i in 1..2) { $i }"; $e = $LASTEXITCODE
"exit=$e"
if ($e -ne 0) """ + YES,
        "ja": {
            "title": "powershell -Command の1行に書いた $変数 が、呼ぶ前に消える",
            "search": ["powershell -Command 変数 消える", "powershell ワンライナー foreach エラー", "-Command 二重引用符 $"],
            "symptom": "powershell -Command \"foreach ($i in 1..2) { $i }\" が構文エラーになる。中身は正しいのに、子の PowerShell には foreach ( in 1..2) が届いている。",
            "why": "二重引用符の中の $i は、呼ぶ側の PowerShell が先に展開する（空になる）。展開済みの文字列が子に渡る。",
            "fix": "処理は .ps1 に書いて -File で呼ぶ。1行で渡すなら単一引用符で囲む。",
            "fixcode": "powershell -NoProfile -File .\\job.ps1\npowershell -NoProfile -Command 'foreach ($i in 1..2) { $i }'",
            "result": "構文エラー、終了コード 1",
        },
        "en": {
            "title": "$variables in a powershell -Command one-liner vanish before it runs",
            "search": ["powershell -Command variable empty", "powershell one-liner foreach syntax error", "powershell -Command variable empty double quotes"],
            "symptom": "powershell -Command \"foreach ($i in 1..2) { $i }\" fails with a syntax error. The code is fine; the child PowerShell received foreach ( in 1..2).",
            "why": "Inside double quotes the calling PowerShell expands $i first (to nothing) and passes the result to the child.",
            "fix": "Put the logic in a .ps1 and run it with -File. For a one-liner, use single quotes.",
            "fixcode": "powershell -NoProfile -File .\\job.ps1\npowershell -NoProfile -Command 'foreach ($i in 1..2) { $i }'",
            "result": "syntax error, exit 1",
        },
    },
    {
        "id": "t11",
        "check": HEAD + r"""New-Item -ItemType Directory "$d\inc" -Force | Out-Null
[IO.File]::WriteAllText("$d\inc\a.ps1", 'x'); [IO.File]::WriteAllText("$d\inc\b.md", 'x')
$n = @(Get-ChildItem -LiteralPath "$d\inc" -Recurse -File -Include *.ps1).Count
"matched $n files for -Include *.ps1 (expected 1)"
if ($n -eq 2) """ + YES,
        "ja": {
            "title": "Get-ChildItem の -Include が効かず、全部のファイルが返る",
            "search": ["Get-ChildItem Include 効かない", "LiteralPath Include 無視", "Get-ChildItem 拡張子 絞り込み できない"],
            "symptom": "Get-ChildItem -LiteralPath $dir -Recurse -Include *.ps1 なのに、.md や .json まで返る。後ろの処理が関係ないファイルまで触る。",
            "why": "Windows PowerShell 5.1 では、-LiteralPath と -Include を一緒に使うと -Include が無視される。エラーは出ない。",
            "fix": "-Include を使わず、Where-Object で拡張子を絞る。",
            "fixcode": "Get-ChildItem -LiteralPath $dir -Recurse -File |\n  Where-Object { $_.Extension -eq '.ps1' }",
            "result": ".md も返った（2件）",
        },
        "en": {
            "title": "Get-ChildItem -Include is ignored and every file comes back",
            "search": ["Get-ChildItem -Include not working", "-LiteralPath -Include ignored", "Get-ChildItem filter extension returns all files"],
            "symptom": "Get-ChildItem -LiteralPath $dir -Recurse -Include *.ps1 also returns .md and .json files, and whatever runs next touches them.",
            "why": "In Windows PowerShell 5.1, -Include is ignored when combined with -LiteralPath. No error.",
            "fix": "Do not use -Include. Filter with Where-Object.",
            "fixcode": "Get-ChildItem -LiteralPath $dir -Recurse -File |\n  Where-Object { $_.Extension -eq '.ps1' }",
            "result": "the .md came back too (2 files)",
        },
    },
    {
        "id": "t12",
        "check": HEAD + r"""$t = "use `night-shift and `true."
$t
if ($t -match "`n" -or $t -match "`t") """ + YES,
        "ja": {
            "title": "PowerShell の \"...\" に書いた Markdown のバッククォートで、文字が消えて改行が入る",
            "search": ["PowerShell バッククォート 消える", "ヒアストリング Markdown 文字化け", "PowerShell `n 改行 勝手に"],
            "symptom": "\"...\" や @\"...\"@ に `night-shift` のようなコード表記を書くと、n が消えて改行になる。`true` なら t が消えてタブ。エラーは出ず、ファイルの一部が欠けるだけ。",
            "why": "バッククォートは PowerShell のエスケープ文字。`n は改行、`t はタブ、`0 は NUL として解釈される。",
            "fix": "バッククォートを含む文章は単一引用符のヒアストリング @'...'@ に書き、差し込みは .Replace() で行う。書いたら出力を読み返す。",
            "fixcode": "$tpl = @'\nuse `night-shift` and `NAME`.\n'@\n$text = $tpl.Replace('NAME', $name)",
            "result": "改行が入った",
        },
        "en": {
            "title": "Markdown backticks inside PowerShell \"...\" turn into newlines and tabs",
            "search": ["powershell backtick n newline in string", "powershell markdown backtick disappearing", "powershell string missing characters backtick"],
            "symptom": "You write `night-shift` or `true` in a \"...\" string or @\"...\"@ here-string. The n or t disappears and a newline or tab appears. No error; part of the file is just missing.",
            "why": "The backtick is PowerShell's escape character: `n is a newline, `t a tab, `0 a NUL.",
            "fix": "Put text with backticks in a single-quoted here-string @'...'@ and insert values with .Replace(). Read the output back.",
            "fixcode": "$tpl = @'\nuse `night-shift` and `NAME`.\n'@\n$text = $tpl.Replace('NAME', $name)",
            "result": "a newline appeared",
        },
    },
    {
        "id": "t13",
        "slow": True,
        "check": HEAD + r"""$ad = Join-Path $env:LOCALAPPDATA ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $ad -Force | Out-Null
$log = Join-Path $ad 'w.log'; [IO.File]::WriteAllText($log, '')
[IO.File]::WriteAllText("$d\writer.py", "import sys,time`nf=open(sys.argv[1],'a')`nf.write('x'*5000000)`nf.flush()`ntime.sleep(20)`nf.close()`n")
$p = Start-Process python -ArgumentList "`"$d\writer.py`"", "`"$log`"" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5
$listed = (Get-ChildItem -LiteralPath $ad -Filter 'w.log').Length
$fs = [IO.File]::Open($log, 'Open', 'Read', 'ReadWrite'); $real = $fs.Length; $fs.Close()
$p.WaitForExit(); Remove-Item -LiteralPath $ad -Recurse -Force
"listed=$listed real=$real"
if ($listed -ne $real) """ + YES,
        "ja": {
            "title": "Windows の PowerShell で書き込み中のログが 0 バイトに見える",
            "search": ["ログ 0バイト 書き込み中", "Get-ChildItem Length 0 なのに", "ファイルサイズ 更新されない Windows"],
            "symptom": "常駐プロセスが書いているログを Get-ChildItem で見ると 0 バイト。「何も出ていない」と判断したら、実際は数 MB 書かれていた。",
            "why": "Windows は、開いたまま書き続けているファイルの一覧上のサイズを、すぐには更新しないことがある（作者の PC では AppData の下で再現）。",
            "fix": "空かどうかを判断する前に、ファイルを開いて長さを読む。",
            "fixcode": "$fs = [IO.File]::Open($log, 'Open', 'Read', 'ReadWrite')\n$fs.Length; $fs.Close()",
            "result": "一覧では 0、実際は 5,000,000 バイト",
        },
        "en": {
            "title": "A log that is being written shows 0 bytes in PowerShell on Windows",
            "search": ["file size shows 0 while writing windows", "powershell file size 0 while writing", "log file size not updating windows"],
            "symptom": "A log written by a running process shows 0 bytes in Get-ChildItem. You conclude nothing was written; in fact it holds megabytes.",
            "why": "Windows may not update the listed size of a file that is still open for writing (reproduced under AppData on the author's machine).",
            "fix": "Open the file and read its length before concluding it is empty.",
            "fixcode": "$fs = [IO.File]::Open($log, 'Open', 'Read', 'ReadWrite')\n$fs.Length; $fs.Close()",
            "result": "listed 0, actual 5,000,000 bytes",
        },
    },
    {
        "id": "t14",
        "claude": True,
        "check": HEAD + r"""$o = claude -p --allowedTools Read 'say hi' 2>&1 | Out-String
($o.Trim() -split "`n")[0]
if ($o -match 'Input must be provided') """ + YES,
        "ja": {
            "title": "claude -p --allowedTools の後ろに書いたプロンプトが飲み込まれる",
            "search": ["Input must be provided either through stdin or as a prompt argument", "claude -p allowedTools プロンプト", "claude -p --add-dir エラー"],
            "symptom": "claude -p --allowedTools Read \"要約して\" が「Input must be provided either through stdin or as a prompt argument」で止まる。プロンプトは書いてあるのに。",
            "why": "--allowedTools と --add-dir は値をいくつでも取る。後ろに置いたプロンプトも、許可するツールの名前として飲み込まれる。",
            "fix": "プロンプトは位置引数で渡さず、標準入力から渡す。",
            "fixcode": "'Summarize README.md' | claude -p --allowedTools Read",
            "result": "Input must be provided ... で止まった",
        },
        "en": {
            "title": "claude -p --allowedTools swallows the prompt after it",
            "search": ["Input must be provided either through stdin or as a prompt argument", "claude -p allowedTools prompt ignored", "claude code --add-dir prompt error"],
            "symptom": "claude -p --allowedTools Read \"summarize this\" stops with \"Input must be provided either through stdin or as a prompt argument\", although the prompt is right there.",
            "why": "--allowedTools and --add-dir take any number of values. The prompt placed after them is taken as one more tool name.",
            "fix": "Send the prompt on stdin instead of as a positional argument.",
            "fixcode": "'Summarize README.md' | claude -p --allowedTools Read",
            "result": "stopped with Input must be provided ...",
        },
    },
    {
        "id": "h01",
        "claude": True,
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\slow-deny.ps1", '[IO.File]::WriteAllText(''MARK'', ''x''); Start-Sleep -Seconds 15; [Console]::Error.WriteLine("denied"); exit 2'.Replace('MARK', "$d\called.txt"))
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -File \"' + ($d -replace '\\', '/') + '/slow-deny.ps1\"'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK","timeout":3}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"; $c = Test-Path "$d\called.txt"
"hook denies after 15 s, timeout 3 s: hook called=$c, written=$w"
if (-not $c) { 'CANNOT CHECK (the hook was never called: check disableAllHooks or your settings)' } elseif ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }""",
        "ja": {
            "title": "Claude Code の PreToolUse フックが、タイムアウト（時間切れ）になると書き込みを止めずに通す",
            "search": ["Claude Code フック 効かない", "PreToolUse フック タイムアウト", "Claude Code hook 素通り", "onFailure block"],
            "symptom": "書き込みを拒否するフックを入れてあるのに、ファイルが書かれた。画面にも結果の JSON にもエラーや警告は出ない。フックの答えが時間制限より遅れたときだけ起きる。",
            "why": "既定では、フックが時間切れ・異常終了・起動失敗になると、Claude Code はツールの呼び出しを止めずに先へ進める。公式の hooks リファレンスにも「止まったフックを関所として当てにしない」とある。ただし Git Bash が入っていない Windows では、onFailure を付けていないフックでも、失敗や時間切れで止まる側に倒れることがある（同じ説明書）。作者の PC には Git Bash が入っている。",
            "fix": "関所のフックに \"onFailure\": \"block\" を付ける（Claude Code 2.1.295 以降）。付けたら、フックが動かない PC では書き込みが全部止まるので、1回試す。時間制限は短くしすぎない。",
            "fixcode": "{\"type\": \"command\", \"command\": \"...\", \"timeout\": 60, \"onFailure\": \"block\"}",
            "result": "15秒待って拒否するフックを時間制限3秒で試し、2回とも書き込まれた。onFailure: block を足すと止まった",
        },
        "en": {
            "title": "A Claude Code PreToolUse hook lets the write through when it times out",
            "search": ["claude code hook not blocking", "PreToolUse hook timeout write goes through", "claude code hook fail open", "onFailure block"],
            "symptom": "You have a hook that denies writes, yet the file was written. No error or warning on screen or in the JSON result. It happens only when the hook answers later than its timeout.",
            "why": "By default, when a hook times out, crashes or cannot start, Claude Code lets the tool call continue. The official hooks reference says not to count on a stalled hook as a gate. On Windows without Git Bash, though, a failed or timed-out hook without onFailure can block instead (same reference); the author's machine has Git Bash.",
            "fix": "Add \"onFailure\": \"block\" to gate hooks (Claude Code 2.1.295 or later). Then a hook that cannot run blocks every write, so test it once. Do not make the timeout too short.",
            "fixcode": "{\"type\": \"command\", \"command\": \"...\", \"timeout\": 60, \"onFailure\": \"block\"}",
            "result": "a hook that denies after 15 s with a 3 s timeout let the write through twice; with onFailure: block it was blocked",
        },
    },
    {
        "id": "h02",
        "claude": True,
        "check": HEAD + r"""[IO.File]::WriteAllText("$d\deny.ps1", '[IO.File]::WriteAllText(''MARK'', ''x''); [Console]::Error.WriteLine("denied"); exit 2'.Replace('MARK', "$d\called.txt"))
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -Command \"& ''' + ($d -replace '\\', '/') + '/deny.ps1''\"'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"; $c = Test-Path "$d\called.txt"
"deny hook called through -Command: hook called=$c, written=$w"
if (-not $c) { 'CANNOT CHECK (the hook was never called: check disableAllHooks or your settings)' } elseif ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }""",
        "ja": {
            "title": "PowerShell のフックを -Command で呼ぶと、Claude Code の拒否が素通りする",
            "search": ["Claude Code フック PowerShell", "PreToolUse exit 2 効かない", "Claude Code hook powershell -Command", "フック 拒否 されない"],
            "symptom": "exit 2 で拒否する PowerShell スクリプトをフックにしたのに、書き込みが通る。スクリプトを手で動かすと確かに 2 を返す。",
            "why": "フックの拒否は終了コード 2。powershell -Command \"& 'deny.ps1'\" で呼ぶと、2 が 1 に化ける（T01 と同じ）。1 は「止めないエラー」なので、書き込みは進む。Git Bash が入っていない Windows では、失敗が止める側に倒れることがあり、そこではこの穴は出ない見込み（公式の説明書。作者の PC には Git Bash が入っている）。",
            "fix": "PowerShell のフックは -File で呼ぶ。念のため \"onFailure\": \"block\" も付ける（-Command のままでも、これで止まった）。",
            "fixcode": "\"command\": \"powershell -NoProfile -ExecutionPolicy Bypass -File C:/hooks/deny.ps1\",\n\"onFailure\": \"block\"",
            "result": "-File は止まった／-Command は書き込まれた／-Command に onFailure: block を足すと止まった",
        },
        "en": {
            "title": "A PowerShell hook called with -Command does not block Claude Code",
            "search": ["claude code hook powershell exit code 2", "PreToolUse exit 2 not blocking windows", "claude code powershell hook -Command", "claude code hook deny ignored"],
            "symptom": "Your hook is a PowerShell script that exits 2 to deny, yet writes go through. Run by hand, the script does return 2.",
            "why": "A hook denies with exit code 2. Called as powershell -Command \"& 'deny.ps1'\", the 2 becomes 1 (same as T01), and 1 is a non-blocking error, so the write proceeds. On Windows without Git Bash a failure can block instead, so this is not expected there (official reference; the author's machine has Git Bash).",
            "fix": "Call PowerShell hooks with -File. Also add \"onFailure\": \"block\" (it blocked even with -Command).",
            "fixcode": "\"command\": \"powershell -NoProfile -ExecutionPolicy Bypass -File C:/hooks/deny.ps1\",\n\"onFailure\": \"block\"",
            "result": "-File blocked / -Command let the write through / -Command with onFailure: block blocked",
        },
    },
]


TRAPS.append({
    "id": "h03",
    "claude": True,
    "check": HEAD + r"""foreach ($f in @("$env:USERPROFILE\.claude\settings.json", "$PWD\.claude\settings.json", "$PWD\.claude\settings.local.json")) {
  if (Test-Path -LiteralPath $f) { try { $v = (Get-Content -LiteralPath $f -Raw -Encoding UTF8 | ConvertFrom-Json).disableAllHooks; "your settings: $f -> disableAllHooks=$v" } catch { "your settings: $f -> not valid JSON" } }
}
[IO.File]::WriteAllText("$d\deny.ps1", '[IO.File]::WriteAllText(''MARK'', ''x''); [Console]::Error.WriteLine("denied"); exit 2'.Replace('MARK', "$d\called.txt"))
$hook = 'powershell -NoProfile -ExecutionPolicy Bypass -File \"' + ($d -replace '\\', '/') + '/deny.ps1\"'
[IO.File]::WriteAllText("$d\s.json", '{"disableAllHooks":true,"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK","onFailure":"block"}]}]}}'.Replace('HOOK', $hook))
Push-Location $d
'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
Pop-Location
$w = Test-Path "$d\written.txt"; $c = Test-Path "$d\called.txt"
"deny hook with onFailure block, plus disableAllHooks true: hook called=$c, written=$w"
if ((-not $c) -and $w) """ + YES,
    "ja": {
        "title": "Claude Code のフックが1つも動かない（disableAllHooks が残っている）",
        "search": ["Claude Code フック 動かない", "Claude Code hook 実行されない", "disableAllHooks", "PreToolUse 呼ばれない"],
        "symptom": "書き込みを止めるフックも、通知のフックも、何も動かない。エラーも警告も出ない。試しに一時的に止めたつもりの設定が、そのまま残っていることがある。",
        "why": "設定ファイルに \"disableAllHooks\": true があると、Claude Code はそのファイルが効く範囲のフックを全部動かさない（管理者の設定で入れたフックは除く）。値は設定の優先順位で決まり、あなた用の設定（~/.claude/settings.json）で true でも、プロジェクトの設定で false なら動く。onFailure: \"block\" を付けた安全装置も、呼ばれないので止めない。",
        "fix": "その行を消す（または false にする）。確かめるコードの最初の行に、あなたの設定ファイルごとの値が出る。1回だけフックを外して動かしたいなら、設定ファイルに書かずに、コマンドの --settings で渡す。",
        "fixcode": "claude -p --settings '{\"disableAllHooks\": true}'   # その1回だけ止める（ファイルには残らない）",
        "result": "拒否するフック（onFailure: block 付き）を入れても、disableAllHooks: true と一緒だと、フックは呼ばれず書き込まれた",
    },
    "en": {
        "title": "No Claude Code hook runs at all (disableAllHooks is still set)",
        "search": ["claude code hooks not running", "claude code hook not triggered", "disableAllHooks", "PreToolUse hook never called"],
        "symptom": "Your write guard, your notification hook, nothing runs. No error, no warning. A setting you added to pause hooks for a moment may still be there.",
        "why": "With \"disableAllHooks\": true in a settings file, Claude Code runs none of the hooks that file reaches (managed-policy hooks excepted). The value follows settings precedence: true in your user settings (~/.claude/settings.json) is overridden by false in the project's settings. A guard with onFailure: \"block\" does not help, because it is never called.",
        "fix": "Remove the line (or set it to false). The first lines of the check print the value in each of your settings files. To skip hooks for a single run, pass it on the command line with --settings instead of writing it to a file.",
        "fixcode": "claude -p --settings '{\"disableAllHooks\": true}'   # skips hooks for this run only; nothing is saved",
        "result": "a denying hook with onFailure: block, together with disableAllHooks: true, was never called and the file was written",
    },
})

TRAPS.append({
    "id": "h04",
    "claude": True,
    "check": HEAD + r"""$jp = [string][char]0x65E5 + [char]0x672C + [char]0x8A9E
$t = Join-Path $d $jp; New-Item -ItemType Directory $t -Force | Out-Null
$py = & python -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1
if (-not $py) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
[IO.File]::WriteAllText("$d\deny_all.py", "import sys, json`nopen(r'MARK', 'w').close()`ndata = json.load(sys.stdin)`nprint(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': 'deny_all'}}))`n".Replace('MARK', "$d\called.txt"))
$hook = '\"' + ($py -replace '\\', '/') + '\" \"' + ($d -replace '\\', '/') + '/deny_all.py\"'
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
[IO.File]::WriteAllText("$d\prompt.md", "Use the Write tool once to create the file $t\written.txt with the content hi. Do not retry if it is blocked.", (New-Object Text.UTF8Encoding $false))
Push-Location $d
"Read the file $d\prompt.md and do exactly what it says." | claude -p --settings s.json --permission-mode acceptEdits --allowedTools "Read,Write" | Out-Null
Pop-Location
$w = Test-Path "$t\written.txt"; $c = Test-Path "$d\called.txt"
"deny-all Python hook, target folder with a Japanese name: hook called=$c, written=$w"
if (-not $c) { 'CANNOT CHECK (the hook was never called: check disableAllHooks or your settings)' } elseif ($w) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}""",
    "ja": {
        "title": "Python で書いた Claude Code の拒否フックが、日本語のフォルダでだけ書き込みを通す",
        "search": ["Claude Code フック 日本語 パス", "PreToolUse python 文字化け", "json.load sys.stdin cp932", "Invalid \\escape JSONDecodeError 日本語", "Claude Code hook 素通り 日本語"],
        "symptom": "書き込みを全部拒否するフックを Python で書いた。英数字のフォルダでは止まるのに、名前が日本語のフォルダへの書き込みは通る。エラーも警告も出ない。",
        "why": "Claude Code はフックの標準入力に UTF-8 の JSON を送る。日本語 Windows の Python は、標準入力が端末でないとき cp932 で読むので、json.load(sys.stdin) が日本語のパスで JSONDecodeError（Invalid \\escape）になる。「語」の UTF-8 の最後のバイトが cp932 の2バイト文字の1バイト目と読まれ、後ろの \\ を巻き込むため。フックが例外で落ちた終了コード 1 は「止めない失敗」なので、onFailure を付けていなければ書き込みは進む。",
        "fix": "標準入力をバイト列のまま読んで UTF-8 で解く。あわせて \"onFailure\": \"block\" を付ける（直す前のフックのままでも、これで止まった）。拒否の理由は ASCII で出す（json.dumps の既定のまま）。",
        "fixcode": "import sys, json\ndata = json.loads(sys.stdin.buffer.read().decode(\"utf-8\"))",
        "result": "同じ拒否フックで、英数字のフォルダは止まり、日本語のフォルダは書き込まれた。onFailure: block を足すと止まった（2026-10-24、Claude Code 2.1.310）",
    },
    "en": {
        "title": "A Python deny hook lets Claude Code write into a folder with a non-ASCII (Japanese) name",
        "search": ["claude code hook non-ascii path", "PreToolUse python hook unicode path", "json.load sys.stdin windows encoding", "JSONDecodeError Invalid \\escape hook", "claude code hook bypass japanese folder"],
        "symptom": "You wrote a Python hook that denies every write. It blocks writes into an ASCII folder, but a write into a folder with a Japanese name goes through. No error, no warning.",
        "why": "Claude Code sends UTF-8 JSON to the hook's stdin. On Japanese Windows, Python reads a non-console stdin as cp932, so json.load(sys.stdin) raises JSONDecodeError (Invalid \\escape) on a Japanese path: the last UTF-8 byte of a character is read as a cp932 lead byte and swallows the following backslash. The hook crashes with exit code 1, a non-blocking error, so without onFailure the write proceeds. Other non-UTF-8 code pages can mangle the input in similar ways.",
        "fix": "Read stdin as bytes and decode it as UTF-8. Also add \"onFailure\": \"block\" (it blocked even with the unfixed hook). Keep the deny reason ASCII (json.dumps default).",
        "fixcode": "import sys, json\ndata = json.loads(sys.stdin.buffer.read().decode(\"utf-8\"))",
        "result": "the same deny hook blocked the ASCII folder and let the Japanese-named folder through; with onFailure: block it blocked (2026-10-24, Claude Code 2.1.310)",
    },
})

TRAPS.append({
    "id": "h05",
    "claude": True,
    "check": HEAD + r"""$cmd = (@('@echo off', 'more > nul', 'echo x> "MARK"', 'exit /b 2') -join "`r`n").Replace('MARK', "$d\called.txt")
[IO.File]::WriteAllText("$d\deny.cmd", $cmd + "`r`n")
$fwd = '\"' + ($d -replace '\\', '/') + '/deny.cmd\"'
$back = ($d + '\deny.cmd') -replace '\\', '\\'
foreach ($k in @('fwd', 'back')) {
  $w = Join-Path $d $k; New-Item -ItemType Directory $w -Force | Out-Null
  $hook = if ($k -eq 'fwd') { $fwd } else { $back }
  [IO.File]::WriteAllText("$w\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Write|Edit","hooks":[{"type":"command","command":"HOOK"}]}]}}'.Replace('HOOK', $hook))
  Push-Location $w
  'Use the Write tool once to create the file written.txt with the content hi. Do not retry if it is blocked.' | claude -p --settings s.json --permission-mode acceptEdits | Out-Null
  Pop-Location
  if ($k -eq 'fwd') { $c = Test-Path "$d\called.txt" }
}
$wf = Test-Path "$d\fwd\written.txt"; $wb = Test-Path "$d\back\written.txt"
"same deny.cmd: quoted C:/.../deny.cmd -> hook called=$c, written=$wf; unquoted C:\...\deny.cmd -> written=$wb"
if ((-not $c) -or $wf) { 'CANNOT CHECK (the quoted forward-slash hook did not block: check Git for Windows, disableAllHooks or your settings)' } elseif ($wb) { 'REPRODUCED' } else { 'NOT REPRODUCED' }""",
    "ja": {
        "title": "Claude Code のフックのパスを \\ で書くと、フックが起動せず書き込みが通る（終了コード 127）",
        "search": ["Claude Code フック 動かない パス", "Claude Code hook 127", "PreToolUse command not found", "Claude Code フック バックスラッシュ", "フック 空白 パス 動かない"],
        "symptom": "書き込みを拒否するフックを入れたのに、ファイルが書かれた。フックのスクリプトは、手で動かすと確かに拒否する。設定の command に C:\\...\\deny.cmd のような \\ 区切りのパスか、空白入りのパスを囲まずに書いている。エラーも警告も出ない。",
        "why": "Git for Windows が入った Windows では、Claude Code はフックの command を Git Bash のコマンド行として動かす。bash にとって \\ は「次の1文字をそのまま使う」記号なので、C:\\Users\\me\\deny.cmd は C:Usersmedeny.cmd という無いコマンドになる。空白入りのパスは空白で切られる。どちらも終了コード 127（コマンドが見つからない）で、PreToolUse では 0 と 2 以外は「止めないエラー」なので、書き込みは進む。claude -p の結果には何も出ず、--debug のログに status 127 が残る（公式 issue #109103 と同じ）。",
        "fix": "パスは / 区切りで書き、全体を \" で囲む（JSON の中では \\\"）。関所のフックには \"onFailure\": \"block\" も付ける（起動できなかったときも止まる。Claude Code 2.1.295 以降）。",
        "fixcode": "\"command\": \"\\\"C:/Users/me/hooks/deny.cmd\\\"\",\n\"onFailure\": \"block\"",
        "result": "同じ deny.cmd で、/ 区切りは止まり、\\ 区切りと、空白入りを囲まない書き方は書き込まれた（debug に status 127）。onFailure: block を足すと止まった（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "A Claude Code hook path written with backslashes never starts, and the write goes through (exit code 127)",
        "search": ["claude code hook not running windows path", "claude code hook 127", "PreToolUse command not found windows", "claude code hook backslash path", "claude code hook path with spaces"],
        "symptom": "You have a hook that denies writes, yet the file was written. Run by hand, the hook script does deny. The command in your settings is a backslash path such as C:\\...\\deny.cmd, or a path with a space and no quotes. No error, no warning.",
        "why": "With Git for Windows installed, Claude Code runs a hook's command as a Git Bash command line. To bash, \\ escapes the next character, so C:\\Users\\me\\deny.cmd becomes C:Usersmedeny.cmd, a command that does not exist. An unquoted path with a space is split at the space. Both exit with 127 (command not found), and for PreToolUse anything other than 0 or 2 is a non-blocking error, so the write proceeds. Nothing shows in the claude -p result; the --debug log records status 127 (official issue #109103).",
        "fix": "Write the path with forward slashes and wrap it in quotes (\\\" inside JSON). Give gate hooks \"onFailure\": \"block\" too, so a hook that cannot start also blocks (Claude Code 2.1.295 or later).",
        "fixcode": "\"command\": \"\\\"C:/Users/me/hooks/deny.cmd\\\"\",\n\"onFailure\": \"block\"",
        "result": "with the same deny.cmd, the forward-slash path blocked; the backslash path and the unquoted path with a space let the write through (status 127 in the debug log); adding onFailure: block blocked it (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h06",
    "claude": True,
    "check": HEAD + r"""Set-Content -LiteralPath "$d\app.settings.json" -Value old
$short = (cmd /c dir /x "$d" | Select-String 'app\.settings\.json' | ForEach-Object { ($_.Line -split '\s+') | Where-Object { $_ -match '~[0-9]' } } | Select-Object -First 1)
if (-not $short) { 'CANNOT CHECK (no 8.3 short name on this drive: dir /x shows none, so this cannot happen here)' } else {
"short name: $short"
Push-Location $d
"Use the Write tool once to overwrite the file $short in the current folder with the single line new. Use exactly that file name. Do not use any other tool. Do not retry." | claude -p --permission-mode bypassPermissions | Out-Null
Pop-Location
$long = Test-Path -LiteralPath "$d\app.settings.json"
$names = (Get-ChildItem -LiteralPath $d -Force | ForEach-Object { $_.Name }) -join ', '
"after the write: files = $names"
if ((-not $long) -and ($names -match [regex]::Escape($short))) """ + YES + r"""
}""",
    "ja": {
        "title": "Windows の短い名前（8.3）で Claude Code に Write・Edit させると、元のファイル名が消える",
        "search": ["Claude Code ファイル名 変わる", "Claude Code 8.3 短い名前", "ENV~1 ファイル", "Claude Code Write ファイル 消えた", "bypassPermissions Windows"],
        "symptom": "app.settings.json や credentials.json が消えて、APPSET~1.JSO や CREDEN~1.JSO という名前のファイルができている。中身は Claude が書いたとおり。ツールはふつうに成功と返していて、名前が変わったことは言っていない。",
        "why": "Windows のファイルには、長い名前とは別に dir /x で見える短い名前（8.3 形式）が付いていることがある。同じファイルの別名だが、Claude Code の Write・Edit にこの短い名前を渡すと、長い名前のファイルが消え、短い名前そのもののファイルが作られる（公式 issue #110153）。acceptEdits の claude -p では止まったが、確認なしで書き込む bypassPermissions では起きる。",
        "fix": "bypassPermissions は使い捨ての環境だけにする。普段の PC で使うなら、ファイル名の部分に ~数字 があるパスを拒否する PreToolUse フックを入れる（-File で呼び、onFailure: block も付ける）。",
        "fixcode": "$p = [string]$j.tool_input.file_path\nif ((Split-Path $p -Leaf) -match '~[0-9]+') { [Console]::Error.WriteLine('blocked: 8.3 short name'); exit 2 }",
        "result": "bypassPermissions で APPSET~1.JSO に Write すると app.settings.json が消え APPSET~1.JSO ができた。Read と Edit でも同じ。acceptEdits の claude -p では止まった。上のフックを入れると bypassPermissions でも止まった（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "Writing through a Windows 8.3 short name makes Claude Code drop the original file name",
        "search": ["claude code file renamed short name", "claude code 8.3 short name write", "ENV~1 file created", "claude code write file disappeared windows", "bypassPermissions windows short name"],
        "symptom": "app.settings.json or credentials.json is gone, and a file named APPSET~1.JSO or CREDEN~1.JSO is there instead, with the content Claude wrote. The tool reported success and never mentioned a rename.",
        "why": "A Windows file can carry a second, short name (8.3 format) that dir /x shows. It is an alias for the same file, but when Claude Code's Write or Edit is given the short name, the long-named file is removed and a new file literally named with the short spelling is created (official issue #110153). It was refused in an acceptEdits claude -p run, but happens in bypassPermissions, which writes without asking.",
        "fix": "Keep bypassPermissions to throwaway environments. If you use it on your own machine, add a PreToolUse hook that denies paths whose file-name part contains ~ followed by digits (call it with -File and add onFailure: block).",
        "fixcode": "$p = [string]$j.tool_input.file_path\nif ((Split-Path $p -Leaf) -match '~[0-9]+') { [Console]::Error.WriteLine('blocked: 8.3 short name'); exit 2 }",
        "result": "in bypassPermissions, a Write to APPSET~1.JSO removed app.settings.json and created APPSET~1.JSO; Read and Edit did the same; an acceptEdits claude -p run was refused; with the hook above, it was blocked even in bypassPermissions (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h07",
    "claude": True,
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\p.txt", "Do exactly these steps and nothing else:`n1. Use the Bash tool with run_in_background set to true to run exactly this command: sleep 123 & timeout 124 sleep 122 & sleep 125 | cat`n2. Use the TaskStop tool to stop that background task.`n3. Reply STOPPED and the task id.")
Push-Location $d
$o = Get-Content "$d\p.txt" -Raw | claude -p --allowedTools "Bash,TaskStop" | Out-String
Pop-Location
Start-Sleep -Seconds 3
$left = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'sleep(\.exe)?"?\s+12[235]\b' })
"claude said: $($o.Trim())"
"processes still running after claude -p ended: $($left.Count)"
$left | ForEach-Object { '  ' + $_.ProcessId + ' ' + $_.CommandLine }
'(leftover sleep processes end by themselves within about two minutes)'
if ($o -notmatch 'STOPPED') { 'CANNOT CHECK (claude did not report STOPPED: check that the Bash and TaskStop tools are available and allowed)' } elseif ($left.Count -gt 0) """ + YES,
    "ja": {
        "title": "Claude Code で裏の Bash を TaskStop で止めても、& やパイプで動かしたプロセスが残る",
        "search": ["Claude Code TaskStop プロセス 残る", "Claude Code バックグラウンド 止まらない", "claude -p 終わったのに sleep 残る", "Claude Code Windows 孤児プロセス", "run_in_background 止まらない"],
        "symptom": "Claude Code に裏で動かさせた Bash を TaskStop で止め、claude -p も終わったのに、タスクマネージャーに sleep.exe や cat.exe、timeout.exe が残っている。tail -f や繰り返しだと残り続け、PC が重くなる。翌晩の実行とぶつかることもある。",
        "why": "Windows の Claude Code は、裏で動かした Bash を TaskStop で止めるとき、いちばん上の bash は止めるが、その中で & やパイプで動かしたプロセスまでは止めない（公式 issue #109388）。claude -p が終わっても、それらは Git の usr/bin の下のプロセスとして残る。",
        "fix": "裏で動かすコマンドには timeout を付ける（timeout 20 sleep 301 のように、時間が来れば自分で消える）。ときどき下のコマンドで Git の usr/bin の下のプロセスを一覧にして、残りを探す。夜に無人で回すなら、終わったあとに残ったプロセスを見つけて次の回を止める仕組みを置く。",
        "fixcode": "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '*\\Git\\usr\\bin\\*' } | Select-Object ProcessId, CommandLine",
        "result": "claude -p で裏の Bash に sleep 123 & timeout 124 sleep 122 & sleep 125 | cat を動かして TaskStop で止めさせると、claude -p が終わった3秒後も sleep 3つ・timeout・cat の5つが残った。timeout 20 sleep 301 は TaskStop のあと2つ残り、20秒後に両方消えた（2026-11-24、Claude Code 2.1.330、Git for Windows）",
    },
    "en": {
        "title": "Stopping a background Bash task in Claude Code with TaskStop leaves the processes started with & or a pipe running",
        "search": ["claude code taskstop processes left running", "claude code background bash not killed windows", "claude -p exited but sleep still running", "claude code orphan processes windows", "run_in_background does not stop"],
        "symptom": "You had Claude Code run a Bash command in the background and stop it with TaskStop, and claude -p has exited, but sleep.exe, cat.exe or timeout.exe are still in Task Manager. With tail -f or a loop they never end, slow the PC down, and can collide with the next night's run.",
        "why": "On Windows, when TaskStop stops a background Bash task, Claude Code stops the top bash but not the processes it started with & or a pipe (official issue #109388). They stay running under Git's usr/bin after claude -p exits.",
        "fix": "Give background commands a timeout (timeout 20 sleep 301 removes itself when time is up). From time to time, list the processes under Git's usr/bin with the command below and look for leftovers. For unattended night runs, detect processes left after a run and stop the next run.",
        "fixcode": "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '*\\Git\\usr\\bin\\*' } | Select-Object ProcessId, CommandLine",
        "result": "with sleep 123 & timeout 124 sleep 122 & sleep 125 | cat run as a background Bash task in claude -p and stopped with TaskStop, all five (three sleep, timeout, cat) were still running 3 seconds after claude -p exited; with timeout 20 sleep 301, two were left after TaskStop and both were gone 20 seconds later (2026-11-24, Claude Code 2.1.330, Git for Windows)",
    },
})

TRAPS.append({
    "id": "h08",
    "claude": True,
    "check": HEAD + r"""Push-Location $d
git init -q 2>$null
git -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty -m init 2>$null
'Reply with the single word OK.' | claude -w e1 -p | Out-Null
$list = git worktree list --porcelain 2>$null | Out-String
Pop-Location
$wt = ([regex]::Matches($list, '(?m)^worktree ')).Count
$lock = $list -match 'locked claude'
"worktrees: $wt; lock line after claude -p ended: $lock"
($list -split "`n") | Where-Object { $_ -match '^locked' }
if ($wt -lt 2) { 'CANNOT CHECK (claude -w did not make a worktree: check that git is installed and claude -w works here)' } elseif ($lock) """ + YES,
    "ja": {
        "title": "claude -w -p が終わったあとも、git の worktree のロックが残って消せない",
        "search": ["claude -w worktree locked", "git worktree remove locked claude session", "Claude Code worktree 消せない", "cannot remove a locked working tree", "claude --worktree ロック"],
        "symptom": "claude -w で作った worktree を git worktree remove で消そうとすると「locked working tree」と断られる。git worktree prune でも残る。claude -p は終了コード 0 で終わっている。夜に回すたびに worktree が溜まっていく。",
        "why": "claude -w は、作った worktree に「claude session e1 (pid …)」というロックを付ける。-p で動かすと、終わったあともこのロックを外さない（公式 issue #111811）。git はロックの付いた worktree を remove も prune もしない。",
        "fix": "片付ける前に、git worktree list --porcelain の locked の行の pid がもう動いていないかを確かめ、動いていないものだけ git worktree unlock してから remove する。動いている pid のロックは外さない。未コミットの変更が無いかも先に見る。",
        "fixcode": "git worktree list --porcelain\n# locked claude session ... (pid 1234) の 1234 が\nGet-Process -Id 1234 -ErrorAction SilentlyContinue\n# 何も出なければ\ngit worktree unlock <path>\ngit worktree remove <path>",
        "result": "claude -w e1 -p と claude -w -p のどちらでも、終わった pid のロックのまま worktree が残り、git worktree remove が断られた。終わった pid のロックだけ外すと片付いた（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "After claude -w -p exits, the git worktree stays locked and cannot be removed",
        "search": ["claude -w worktree locked", "git worktree remove locked claude session", "claude code worktree cannot remove", "cannot remove a locked working tree", "claude --worktree lock left"],
        "symptom": "git worktree remove refuses a worktree made by claude -w with a locked working tree error, and git worktree prune leaves it too. claude -p exited with code 0. Every night run adds one more worktree.",
        "why": "claude -w locks the worktree it makes with claude session e1 (pid ...). Run with -p, it does not remove that lock when it exits (official issue #111811). git neither removes nor prunes a locked worktree.",
        "fix": "Before cleaning up, check that the pid on the locked line of git worktree list --porcelain is no longer running, and only then git worktree unlock and remove it. Do not unlock worktrees whose pid is still running, and check for uncommitted changes first.",
        "fixcode": "git worktree list --porcelain\n# for locked claude session ... (pid 1234)\nGet-Process -Id 1234 -ErrorAction SilentlyContinue\n# if nothing is shown\ngit worktree unlock <path>\ngit worktree remove <path>",
        "result": "with both claude -w e1 -p and claude -w -p, the worktree stayed locked to the pid of the exited process and git worktree remove refused it; unlocking only the locks of exited pids cleaned it up (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h09",
    "claude": True,
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\p1.txt", 'Run exactly this Bash command and nothing else, then stop: echo ''a$$(b'' > x.txt')
[IO.File]::WriteAllText("$d\p2.txt", 'Run exactly this Bash command and nothing else, then stop: echo ''a$(b'' > y.txt')
Push-Location $d
Get-Content "$d\p2.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Get-Content "$d\p1.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Pop-Location
$y = Test-Path "$d\y.txt"; $x = Test-Path "$d\x.txt"
"echo with one dollar and a paren -> written=$y; echo with two dollars and a paren -> written=$x"
if (-not $y) { 'CANNOT CHECK (even the one-dollar command did not run: check that the Bash tool is available and allowed)' } elseif (-not $x) { 'REPRODUCED' } else { 'NOT REPRODUCED' }""",
    "ja": {
        "title": "Claude Code の Bash ツールで、$$( を含むコマンドが「削除の安全確認」で止まる",
        "search": ["Claude Code can't rule out a dangerous removal", "Claude Code Bash 止まる rm", "Claude Code $$( 拒否", "Claude Code heredoc 拒否", "bypassPermissions でも止まる"],
        "symptom": "削除をしていないのに、Bash ツールの呼び出しが「危ない削除かもしれない」という確認で止まり、コマンドが動かない。コマンドの中に $$( という並び（ドル記号2つと丸括弧）がある。確認なしで動くモード（bypassPermissions）でも止まる。",
        "why": "Claude Code は、Bash のコマンドを実行する前に、消しすぎる削除が無いかを調べる。$$( が入ると、シェルがどう読むかを Claude Code が確かめきれず、削除かもしれないとして止める（公式 issue #108970）。$( が1つだけなら通る。",
        "fix": "$$( を含む本文は、コマンドに直接書かず、Write ツールでファイルに保存してから使う。どうしてもコマンドに書くなら、\"a\\$\\$(b\" のようにドル記号の前にバックスラッシュを置く。",
        "fixcode": "# Write ツールでファイルに保存してから使う\n# どうしてもコマンドに書くなら\necho \"a\\$\\$(b\"",
        "result": "echo 'a$(b' > y.txt は通り、echo 'a$$(b' > x.txt は削除の確認で止まって x.txt ができなかった（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "A Claude Code Bash command containing $$( is stopped by the dangerous-removal check",
        "search": ["claude code can't rule out a dangerous removal", "claude code bash blocked rm check", "claude code $$( denied", "claude code heredoc blocked", "blocked even in bypassPermissions"],
        "symptom": "A Bash tool call that deletes nothing is stopped by a check that says it may be a dangerous removal, and the command never runs. The command contains $$( (two dollar signs and a parenthesis). It is stopped even in bypassPermissions.",
        "why": "Before running a Bash command, Claude Code checks it for removals that could delete far too much. With $$( in it, Claude Code cannot be sure how the shell will read the command, so it treats it as a possible removal and stops it (official issue #108970). A single $( goes through.",
        "fix": "Do not put text containing $$( in a command. Save it to a file with the Write tool first. If it must be in a command, escape the dollars: \"a\\$\\$(b\".",
        "fixcode": "# save the text with the Write tool first\n# if it must be in a command\necho \"a\\$\\$(b\"",
        "result": "echo 'a$(b' > y.txt ran; echo 'a$$(b' > x.txt was stopped by the removal check and x.txt was not created (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h10",
    "claude": True,
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\p.txt", 'Use the Bash tool once to run exactly this command and nothing else, then stop: printf ''%s'' ''a\\b'' > out.bin')
Push-Location $d
Get-Content "$d\p.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Pop-Location
if (-not (Test-Path "$d\out.bin")) { 'CANNOT CHECK (out.bin was not written: check that the Bash tool is available and allowed)' } else {
$b = [IO.File]::ReadAllBytes("$d\out.bin")
"asked for a, two backslashes, b -> bytes written: " + (($b | ForEach-Object { '{0:x2}' -f $_ }) -join ' ')
if ($b.Length -eq 3) """ + YES + r"""
}""",
    "ja": {
        "title": "Windows の Claude Code の Bash ツールで、\\\\（バックスラッシュ2つ）が \\ 1つになる",
        "search": ["Claude Code Bash バックスラッシュ 消える", "Claude Code Windows backslash", "Claude Code ヒアドキュメント 壊れる", "Claude Code 正規表現 壊れる", "Git Bash バックスラッシュ 1つ"],
        "symptom": "Claude Code に Bash ツールで書かせたスクリプトや正規表現で、\\\\ のはずの所が \\ 1つになっている。単引用符の中でも、引用符付きのヒアドキュメントの中でも起きる。エラーは出ず、壊れた中身のまま動く。",
        "why": "Windows（Git for Windows）の Claude Code の Bash ツールは、渡されたコマンドの中の \\\\ を \\ 1つに変えてから実行する。モデルが送ったコマンドには2つ入っている（会話の記録で確かめられる）。4つは2つになり、1つは1つのまま（公式 issue #110308）。",
        "fix": "バックスラッシュを含む本文（スクリプト・正規表現・Windows のパス）は、Bash のコマンドやヒアドキュメントに書かず、Write ツールでファイルに保存してから使う。Windows のパスは / 区切りで書く。",
        "fixcode": "# 本文は Write ツールでファイルに保存し、コマンドではファイルを読むだけにする\npython fix.py",
        "result": "printf '%s' 'a\\\\b' > out.bin で、out.bin は a \\ b の3バイトだった（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "On Windows, Claude Code's Bash tool turns \\\\ (two backslashes) into one",
        "search": ["claude code bash backslash disappears windows", "claude code double backslash becomes single", "claude code heredoc backslash broken", "claude code regex backslash windows", "git bash backslash claude code"],
        "symptom": "A script or regular expression that Claude Code wrote through the Bash tool has \\ where it should have \\\\. It happens inside single quotes and inside quoted heredocs. No error; the broken text just runs.",
        "why": "On Windows (Git for Windows), Claude Code's Bash tool turns each \\\\ in the command into a single \\ before running it. The command the model sent has two (the transcript shows it). Four become two, a single one stays single (official issue #110308).",
        "fix": "Do not put text with backslashes (scripts, regular expressions, Windows paths) in Bash commands or heredocs. Save it to a file with the Write tool first, and write Windows paths with forward slashes.",
        "fixcode": "# save the text with the Write tool, and let the command only read the file\npython fix.py",
        "result": "printf '%s' 'a\\\\b' > out.bin wrote the 3 bytes a \\ b (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h12",
    "claude": True,
    "check": HEAD + r"""foreach ($v in @('1', '0')) {
  $w = Join-Path $d "v$v"; New-Item -ItemType Directory "$w\sub" -Force | Out-Null
  [IO.File]::WriteAllText("$w\s.json", '{"env":{"CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR":"VAL","CLAUDE_CODE_USE_POWERSHELL_TOOL":"1"}}'.Replace('VAL', $v))
  $p = 'You must use the PowerShell tool (not Bash). Call 1: Set-Location sub . Call 2 (a separate PowerShell tool call): [IO.File]::WriteAllText("OUT", (Get-Location).Path) . Then stop.'.Replace('OUT', "$w\call2.txt")
  Push-Location $w
  $p | claude -p --settings s.json --allowedTools PowerShell | Out-Null
  Pop-Location
}
$r1 = ''; $r0 = ''
if (Test-Path "$d\v1\call2.txt") { $r1 = (Get-Content "$d\v1\call2.txt" -Raw).Trim() }
if (Test-Path "$d\v0\call2.txt") { $r0 = (Get-Content "$d\v0\call2.txt" -Raw).Trim() }
"second PowerShell call after cd sub: MAINTAIN=1 -> $r1 ; MAINTAIN=0 -> $r0"
if ((-not $r0) -or (-not $r1)) { 'CANNOT CHECK (the PowerShell tool did not run: it needs a Claude Code version with the PowerShell tool)' } elseif (-not $r0.EndsWith('sub')) { 'CANNOT CHECK (even with MAINTAIN=0 the cd did not stay)' } elseif (-not $r1.EndsWith('sub')) { 'REPRODUCED' } else { 'NOT REPRODUCED' }""",
    "ja": {
        "title": "Claude Code の PowerShell ツールで、cd したフォルダが次の呼び出しで元に戻る",
        "search": ["Claude Code PowerShell ツール cd 戻る", "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "Claude Code PowerShell Set-Location 効かない", "Claude Code 作業フォルダ 戻る", "Working directory persists between commands"],
        "symptom": "Claude Code の PowerShell ツールで Set-Location（cd）したのに、次の呼び出しでは最初のフォルダに戻っていて、ファイルが違う場所に書かれる。PowerShell ツールの説明には「作業フォルダは次のコマンドに引き継がれる」と書いてある。",
        "why": "環境変数 CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1 があると、Claude Code は呼び出しのたびに作業フォルダを最初のフォルダに戻す。Bash ツールの説明はこの設定に合わせて変わるが、PowerShell ツールの説明は「引き継がれる」のまま変わらないので、モデルは前の cd が効いている前提で次のコマンドを書く（公式 issue #111705）。",
        "fix": "作業フォルダは呼び出しごとに指定する（絶対パスを使うか、同じ呼び出しの中で Set-Location -ErrorAction Stop してから実行する）。その設定が要らないなら外す。",
        "fixcode": "Set-Location -LiteralPath 'C:/work/sub' -ErrorAction Stop; ./run.ps1",
        "result": "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1 では2回目の呼び出しが最初のフォルダに戻り、0 では sub のままだった（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "Claude Code's PowerShell tool goes back to the start folder on the next call after cd",
        "search": ["claude code powershell tool cd does not persist", "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR powershell", "claude code powershell set-location reset", "claude code working directory reset", "Working directory persists between commands"],
        "symptom": "You ran Set-Location (cd) in Claude Code's PowerShell tool, but the next call is back in the start folder and writes files in the wrong place. The PowerShell tool's own description says the working directory persists between commands.",
        "why": "With the environment variable CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1, Claude Code resets the working directory to the start folder on every call. The Bash tool's description changes to match; the PowerShell tool's description still says it persists, so the model writes the next command assuming the cd took effect (official issue #111705).",
        "fix": "Name the working folder in every call (use absolute paths, or Set-Location -ErrorAction Stop in the same call before running). Remove the setting if you do not need it.",
        "fixcode": "Set-Location -LiteralPath 'C:/work/sub' -ErrorAction Stop; ./run.ps1",
        "result": "with CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1 the second call was back in the start folder; with 0 it stayed in sub (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h11",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory "$d\sub" -Force | Out-Null
$u = $d -replace '\\', '/'
$p = 'Use the Bash tool exactly twice, one command per call. Call 1: cd "U/sub" && pwd > "U/p1.txt" . Call 2: pwd > "U/p2.txt" . Then stop.'.Replace('U', $u)
Push-Location $d
$p | claude -p --allowedTools Bash | Out-Null
Pop-Location
if (-not (Test-Path "$d\p1.txt") -or -not (Test-Path "$d\p2.txt")) { 'CANNOT CHECK (the Bash tool did not run both calls: check that it is available and allowed)' } else {
$p1 = (Get-Content "$d\p1.txt" -Raw).Trim(); $p2 = (Get-Content "$d\p2.txt" -Raw).Trim()
"inside %TEMP%: same call after cd sub -> $p1 ; next call -> $p2"
if (-not $p1.EndsWith('/sub')) { 'CANNOT CHECK (cd did not work even inside the same call)' } elseif (-not $p2.EndsWith('/sub')) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}""",
    "ja": {
        "title": "Windows の Claude Code の Bash ツールで、%TEMP% の下への cd が次の呼び出しで取り消される",
        "search": ["Claude Code Shell cwd was reset", "Claude Code cd 戻る Temp", "Claude Code Bash cd 効かない", "Claude Code %TEMP% cd", "Claude Code 作業フォルダ 戻る"],
        "symptom": "Bash ツールで %TEMP%（AppData\\Local\\Temp）の下のフォルダに cd したのに、次の呼び出しでは元のフォルダに戻っていて、「Shell cwd was reset to ...」と出る。同じ場所でも Temp 以外の隣のフォルダ（AppData\\Local\\Microsoft など）への cd は残る。",
        "why": "Windows の Claude Code の Bash ツールは、呼び出しのあとの作業フォルダが %TEMP% の下だと、起動したフォルダに戻す（公式 issue #110213）。同じ呼び出しの中なら cd は効くので、1回目の呼び出しは正しく動き、2回目から黙って別の場所で動く。",
        "fix": "作業フォルダは呼び出しごとに指定する（絶対パスを使うか、cd と実行を同じ呼び出しに入れる）。使い捨ての作業場所を %TEMP% の下に作るなら、毎回そのフォルダの絶対パスで書く。",
        "fixcode": "cd \"C:/Users/me/AppData/Local/Temp/work\" && ./run.sh   # cd と実行を同じ呼び出しに",
        "result": "%TEMP% の下から起動して cd sub すると、同じ呼び出しでは sub、次の呼び出しでは起動したフォルダだった。AppData\\Local から起動したときの cd Microsoft は残った（2026-11-24、Claude Code 2.1.330）",
    },
    "en": {
        "title": "On Windows, a cd into %TEMP% in Claude Code's Bash tool is undone on the next call",
        "search": ["claude code Shell cwd was reset", "claude code cd temp reset windows", "claude code bash cd not persisting", "claude code %TEMP% working directory", "claude code working directory reset"],
        "symptom": "You cd'd into a folder under %TEMP% (AppData\\Local\\Temp) in the Bash tool, but the next call is back in the start folder and prints Shell cwd was reset to .... A cd into a sibling folder outside Temp (AppData\\Local\\Microsoft, for example) sticks.",
        "why": "On Windows, Claude Code's Bash tool sends the shell back to the start folder when the working directory after a call is under %TEMP% (official issue #110213). Inside the same call the cd works, so the first call behaves and later calls silently run somewhere else.",
        "fix": "Name the working folder in every call (use absolute paths, or put the cd and the command in the same call). If you keep a scratch folder under %TEMP%, always use its absolute path.",
        "fixcode": "cd \"C:/Users/me/AppData/Local/Temp/work\" && ./run.sh   # cd and run in the same call",
        "result": "started under %TEMP%, after cd sub the same call was in sub and the next call was back in the start folder; started in AppData\\Local, cd Microsoft stuck (2026-11-24, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h13",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\.claude\agents" | Out-Null
[IO.File]::WriteAllText("$d\.claude\agents\ro.md", "---`nname: ro`ndescription: read-only test agent`ntools: Read`n---`nYou answer questions briefly.`n")
$schema = '{\"type\":\"object\",\"properties\":{\"answer\":{\"type\":\"string\"}},\"required\":[\"answer\"]}'
$q = 'What is 2+2? Reply with the answer.'
Push-Location $d
$a = $q | claude -p --model haiku --json-schema $schema --output-format json | Out-String
$b = $q | claude -p --model haiku --json-schema $schema --agent ro --output-format json | Out-String
Pop-Location
$ha = $a -match '"structured_output"'; $hb = $b -match '"structured_output"'; $ok = $b -match '"subtype":"success"'
"without --agent: structured_output=$ha; with --agent ro: structured_output=$hb, subtype success=$ok"
if (-not $ha) { 'CANNOT CHECK (even without --agent there was no structured_output: check that claude -p works and is logged in)' } elseif ((-not $hb) -and $ok) """ + YES,
    "ja": {
        "title": "claude -p の --json-schema が、道具を絞った --agent を付けると黙って効かない（成功のまま）",
        "search": ["claude -p json-schema structured_output 出ない", "claude --json-schema --agent", "structured_output missing", "Claude Code 構造化出力 空", "claude -p subtype success structured_output"],
        "symptom": "claude -p --json-schema で決まった形の答え（structured_output）を受け取るスクリプトが、--agent を付けた回だけ空の値で進む。終了コードは 0、subtype は success、is_error は false で、エラーは出ない。",
        "why": "--json-schema の答えは、Claude が StructuredOutput という道具を呼んで返す。エージェントの tools: で道具を絞ると、この道具も外れて、Claude はふつうの文で答えて終わる（公式 issue #109393）。",
        "fix": "--json-schema を付けたら、structured_output が無いことを失敗として扱う（subtype や終了コードだけで判断しない）。--json-schema を使う回では、道具を絞ったエージェントを使わない。",
        "fixcode": "$out = $prompt | claude -p --json-schema $schema --output-format json | Out-String\nif ($LASTEXITCODE -ne 0 -or $out -notmatch '\"structured_output\"') { Write-Error 'no structured_output'; exit 1 }",
        "result": "--json-schema だけでは structured_output={answer:4}。tools: Read だけのエージェント（--agent ro）を足すと、終了コード 0・subtype success・is_error false のまま structured_output の項目が無かった。PowerShell 5.1 と Git Bash の両方で同じ（2026-11-25、Claude Code 2.1.330）",
    },
    "en": {
        "title": "claude -p --json-schema silently stops working with an --agent that restricts tools (still reports success)",
        "search": ["claude -p json-schema structured_output missing", "claude --json-schema --agent", "structured_output missing agent tools", "claude code structured output empty", "claude -p subtype success no structured_output"],
        "symptom": "A script that reads the structured answer (structured_output) from claude -p --json-schema gets nothing when --agent is added. Exit code 0, subtype success, is_error false, no error.",
        "why": "The --json-schema answer comes back through a tool named StructuredOutput. When the agent's tools: allowlist restricts tools, that tool is removed too, and Claude answers in plain text (official issue #109393).",
        "fix": "When you pass --json-schema, treat a missing structured_output as a failure instead of trusting subtype or the exit code. Do not use an agent with a tools: allowlist in runs that need --json-schema.",
        "fixcode": "$out = $prompt | claude -p --json-schema $schema --output-format json | Out-String\nif ($LASTEXITCODE -ne 0 -or $out -notmatch '\"structured_output\"') { Write-Error 'no structured_output'; exit 1 }",
        "result": "with --json-schema alone, structured_output was {answer:4}; adding an agent with tools: Read only (--agent ro) gave exit 0, subtype success, is_error false and no structured_output field, from both PowerShell 5.1 and Git Bash (2026-11-25, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h15",
    "claude": True,
    "check": HEAD + r"""$res = @{}
foreach ($case in 'partial', 'plain') {
    $t = Join-Path $d $case
    New-Item -ItemType Directory -Force (Join-Path $t 'sub') | Out-Null
    $lines = 1..30 | ForEach-Object { "Rule $_`: keep files tidy." }
    $lines += 'MARKER: the code word for this folder is PELICAN.'
    [IO.File]::WriteAllText((Join-Path $t 'sub\CLAUDE.md'), ($lines -join "`n") + "`n")
    [IO.File]::WriteAllText((Join-Path $t 'sub\a.txt'), "hello`n")
    $ask = 'Without reading any file again, reply with the code word for the sub folder if any instructions you have contain one, otherwise reply UNKNOWN.'
    if ($case -eq 'partial') { $p = "Do exactly this: 1. Use the Read tool on sub/CLAUDE.md with offset 1 and limit 1. 2. Use the Read tool on sub/a.txt. 3. $ask" }
    else { $p = "Do exactly this: 1. Use the Read tool on sub/a.txt. 2. $ask" }
    Push-Location $t
    $out = $p | claude -p --allowedTools Read --output-format json | Out-String
    Pop-Location
    $res[$case] = $out -match 'PELICAN'
}
"knows the code word: after a partial Read first = $($res['partial']); without it = $($res['plain'])"
if (-not $res['plain']) { 'CANNOT CHECK (even without the partial Read the code word was not known: check that claude -p works and is logged in)' } elseif (-not $res['partial']) """ + YES,
    "ja": {
        "title": "サブフォルダの CLAUDE.md を一部だけ Read すると、残りが黙って読み込まれなくなる",
        "search": ["サブフォルダ CLAUDE.md 読み込まれない", "Claude Code nested CLAUDE.md 効かない", "CLAUDE.md offset limit", "Claude Code CLAUDE.md 一部だけ", "nested_memory"],
        "symptom": "サブフォルダの CLAUDE.md に書いた決まりを、Claude がそのフォルダで作業するときに守らない。会話の中で、その CLAUDE.md を数行だけ読んでいた。エラーも警告も出ない。",
        "why": "サブフォルダの CLAUDE.md は、そのフォルダのほかのファイルを読んだときに読み込まれる（公式の説明書）。ところが、先にその CLAUDE.md を Read で offset・limit を付けて一部だけ読んでいると、全体の読み込みが起きない（公式 issue #111719）。",
        "fix": "親の CLAUDE.md に「サブフォルダの CLAUDE.md は、読むなら全体を読む。offset や limit を付けない」と書く。サブフォルダの CLAUDE.md は短くし、大事な決まりを先頭に置く。",
        "fixcode": "# 親の CLAUDE.md に1行\nサブフォルダの CLAUDE.md は、読むなら全体を読む。offset や limit を付けて一部だけ読まない。",
        "result": "31行の sub/CLAUDE.md の最後の行に合言葉を書いた。sub/a.txt を読むだけなら合言葉を知っていた（会話の記録に nested_memory が1件）。先に CLAUDE.md を offset 1・limit 1 で読むと、sub/a.txt を読んでも UNKNOWN（nested_memory 0件）（2026-11-25、Claude Code 2.1.330）",
    },
    "en": {
        "title": "A partial Read of a subdirectory CLAUDE.md silently stops the rest of it from loading",
        "search": ["claude code nested CLAUDE.md not loaded", "subdirectory CLAUDE.md ignored", "CLAUDE.md offset limit read", "claude code CLAUDE.md partially read", "nested_memory missing"],
        "symptom": "Claude ignores rules from a subdirectory CLAUDE.md while working in that folder. Earlier in the session it read a few lines of that CLAUDE.md. No error, no warning.",
        "why": "A subdirectory CLAUDE.md loads when Claude reads another file in that folder (official docs). If the session first read that CLAUDE.md with offset/limit, the full load never happens (official issue #111719).",
        "fix": "Write in the root CLAUDE.md: read a subdirectory CLAUDE.md in full or not at all, never with offset or limit. Keep subdirectory CLAUDE.md files short with the important rules first.",
        "fixcode": "# one line in the root CLAUDE.md\nRead a subdirectory CLAUDE.md in full or not at all; never with offset or limit.",
        "result": "with the code word on the last line of a 31-line sub/CLAUDE.md, reading only sub/a.txt gave the code word (1 nested_memory entry in the transcript); reading the CLAUDE.md with offset 1, limit 1 first gave UNKNOWN (0 entries) (2026-11-25, Claude Code 2.1.330)",
    },
})

TRAPS.append({
    "id": "h17",
    "claude": True,
    "check": HEAD + r"""$repo = Join-Path $d 'hookrepo'
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
if (-not $ran['root']) { 'CANNOT CHECK (the hook did not run even at the root: check that python and git are installed)' } elseif (-not $ran['sub\deep']) """ + YES,
    "ja": {
        "title": "リポジトリのサブフォルダで Claude Code を起動すると、ルートの .claude/settings.json のフックが効かない",
        "search": ["Claude Code フック 効かない サブフォルダ", "Claude Code settings.json 読まれない", "Claude Code hooks not running subdirectory", "settings.local.json Windows", "claude plugin disabled サブフォルダ"],
        "symptom": "リポジトリの直下の .claude/settings.json に入れた書き込みを止めるフックが、ときどき動かない。動かなかった回は、エディタの端末やスクリプトが、リポジトリの下のフォルダで claude を起動していた。エラーも警告も出ない。",
        "why": "公式の説明書のとおり、共有の .claude/settings.json は起動したフォルダから読む。.claude/settings.local.json はふつうリポジトリの直下のものを使うが、Windows では例外で起動したフォルダのものを使う。local の範囲で入れたプラグインも同じ理由でサブフォルダでは disabled になる（公式 issue #106149）。",
        "fix": "必ず止めたいフックはユーザーの設定（~/.claude/settings.json）に入れる。無人のスクリプトは Push-Location でリポジトリの直下に移ってから claude -p を呼ぶ。",
        "fixcode": "Push-Location C:/work/repo   # .claude/settings.json があるフォルダ\n$prompt | claude -p\nPop-Location",
        "result": "直下の .claude/settings.json の PreToolUse フックは、直下で起動すると動き、sub/deep で起動すると動かなかった。.claude/settings.local.json に置いても同じ（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "Start Claude Code in a repo subfolder and the hooks in the root .claude/settings.json do not run",
        "search": ["claude code hooks not running subdirectory", "claude code settings.json not loaded subfolder", "settings.local.json windows repository root", "claude plugin disabled subfolder windows", "claude code project settings working directory"],
        "symptom": "A hook in the repo root .claude/settings.json that blocks writes sometimes does nothing. In those runs, an editor terminal or a script started claude in a folder below the repo root. No error, no warning.",
        "why": "As documented, the shared .claude/settings.json is read from the folder Claude Code starts in. .claude/settings.local.json normally comes from the repo root, but on Windows it is also read from the starting folder. Plugins installed with --scope local are disabled in subfolders for the same reason (official issue #106149).",
        "fix": "Put hooks that must always run in the user settings (~/.claude/settings.json). In unattended scripts, Push-Location to the repo root before calling claude -p.",
        "fixcode": "Push-Location C:/work/repo   # the folder that holds .claude/settings.json\n$prompt | claude -p\nPop-Location",
        "result": "a PreToolUse hook in the root .claude/settings.json ran when claude was started at the root and did not run when started in sub/deep; the same with .claude/settings.local.json (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "h19",
    "claude": True,
    "check": HEAD + r"""$real = Join-Path $d 'real'
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
if (-not $cwd) { 'CANNOT CHECK (no init line from claude -p: check that claude -p works and is logged in)' } elseif ($cwd -like '*\real\repo') """ + YES + r"""
}""",
    "ja": {
        "title": "ジャンクションの下で Claude Code を起動すると、作業フォルダが本当のパスに置き換わる（フックにも）",
        "search": ["Claude Code ジャンクション パス", "Claude Code cwd 変わる", "mklink /J Claude Code", "Claude Code junction realpath", "フック file_path パスが違う"],
        "symptom": "mklink /J で作ったジャンクションの下のフォルダで Claude Code を起動したのに、Claude が言う作業フォルダも、フックに届く cwd と file_path も、ジャンクションをたどった先の本当のパスになっている。起動したときの綴りで書いたフックの許可の範囲が、当たらなくなる。",
        "why": "Claude Code は、起動したフォルダのジャンクションをたどって、本当のパスを作業フォルダにする（公式 issue #106304。issue によると 2.1.312 までは起動したときの綴りのままだった）。会話の記録の置き場所も本当のパスで決まる。",
        "fix": "フックでは、比べる両側を本当のパスにそろえてから比べる（Python なら os.path.realpath）。許可の範囲は本当のパスで書く。",
        "fixcode": "import os\nok = os.path.normcase(os.path.realpath(target)).startswith(os.path.normcase(os.path.realpath(root)) + os.sep)",
        "result": "link（real を指すジャンクション）の下の link/repo で起動すると、init の cwd は real/repo になり、会話の記録のフォルダも real の綴りだった。Write の前に動くフックにも cwd と file_path が real/repo の綴りで届いた（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "Start Claude Code under a junction and the working folder is silently replaced by the real path (hooks too)",
        "search": ["claude code junction path", "claude code cwd resolved real path", "mklink /J claude code", "claude code hook file_path different path", "claude code working directory junction windows"],
        "symptom": "You started Claude Code in a folder under a junction made with mklink /J, but the working folder Claude reports, and the cwd and file_path your hooks receive, are the real path behind the junction. A hook whose allowed paths use the launch spelling no longer matches.",
        "why": "Claude Code follows the junction in the starting folder and uses the real path as its working folder (official issue #106304; per the issue, 2.1.312 and earlier kept the launch spelling). The transcript folder is named after the real path too.",
        "fix": "In hooks, resolve both sides to the real path before comparing (os.path.realpath in Python), and write allowed paths with the real path.",
        "fixcode": "import os\nok = os.path.normcase(os.path.realpath(target)).startswith(os.path.normcase(os.path.realpath(root)) + os.sep)",
        "result": "started in link/repo, where link is a junction to real, the init cwd was real/repo and the transcript folder used the real spelling; a PreToolUse hook on Write received cwd and file_path under real/repo (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "h14",
    "claude": True,
    "check": HEAD + r"""$hook = @'
import json, sys
from pathlib import Path
d = json.load(sys.stdin)
if d.get("tool_name") != "Bash":
    sys.exit(0)
n = int(Path("n.txt").read_text().strip())
cmd = "printf %s '" + "A" * n + "' > o.txt; echo ok > d.txt"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {"command": cmd}}}))
'@
[IO.File]::WriteAllText("$d\hook.py", $hook)
$hp = ($d + '\hook.py').Replace('\', '/')
[IO.File]::WriteAllText("$d\s.json", '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python \"HP\""}]}]}}'.Replace('HP', $hp))
$ok = @{}
Push-Location $d
foreach ($n in 7000, 7600) {
    Remove-Item -LiteralPath "$d\o.txt", "$d\d.txt" -ErrorAction SilentlyContinue
    [IO.File]::WriteAllText("$d\n.txt", "$n")
    'Use the Bash tool once to run: echo hi . Then stop.' | claude -p --settings s.json --allowedTools Bash | Out-Null
    $ok[$n] = (Test-Path "$d\d.txt")
}
Pop-Location
"a 7000-A command ran to the end: $($ok[7000]); a 7600-A command ran to the end: $($ok[7600])"
if (-not $ok[7000]) { 'CANNOT CHECK (even the 7000-character command did not run: check that python is installed and the Bash tool works)' } elseif (-not $ok[7600]) """ + YES,
    "ja": {
        "title": "Windows の Claude Code の Bash ツールは、7,400 文字ほどを超えるコマンドを動かさない（エラーは「引用符が閉じていない」）",
        "search": ["unexpected EOF while looking for matching", "Claude Code Bash 長いコマンド 動かない", "Claude Code ヒアドキュメント 失敗 Windows", "Git Bash bash -c 8186", "Claude Code Bash tool command too long windows"],
        "symptom": "Claude Code が長いヒアドキュメントやスクリプトを Bash ツールで流すと、何も動かず unexpected EOF while looking for matching という引用符のエラーが返る。コマンドに引用符の間違いは無い。単引用符ばかりの中身なら、1,500 文字ほどのコマンドでも起きる。",
        "why": "Windows の Claude Code は、Bash ツールのコマンドを準備と後始末の部分で包み、bash.exe -c の1つの文字列にして渡す。Git for Windows の bash はこの文字列を 8,186 文字までしか受け取らず、残りを捨てる（公式 issue #102533）。包む部分を引くと、書けるコマンドは作者の PC で 7,400 文字前後。issue によると単引用符は5文字に書き換えられ、1つで5文字ぶん使う。",
        "fix": "長いスクリプトやヒアドキュメントは、Write ツールでファイルに書いてから bash script.sh のように短いコマンドで動かす。CLAUDE.md にもそう書いておく。",
        "fixcode": "# CLAUDE.md\n- Windows では Bash ツールのコマンドに長いスクリプトやヒアドキュメントを書かない（上限は 7,000 文字台、単引用符は1つで5文字ぶん）\n- 数千文字を超えそうなものは Write ツールでファイルに書いてから bash <ファイル> で動かす",
        "result": "Bash ツールに渡るコマンドを PreToolUse フックで差し替えると、7,417 文字は動き、7,421 文字は何も動かなかった。単引用符 1,450 個（1,495 文字）は動き、1,500 個（1,545 文字）は動かなかった。9,000 文字の中身をファイルに書いて bash big.sh は動いた（2026-11-25、Claude Code 2.1.330、Git for Windows 2.56.0）",
    },
    "en": {
        "title": "On Windows, Claude Code's Bash tool does not run commands longer than about 7,400 characters (the error says a quote is unmatched)",
        "search": ["unexpected EOF while looking for matching claude code", "claude code bash long command fails windows", "claude code heredoc fails windows", "git bash bash -c 8186 characters", "claude code bash tool command too long"],
        "symptom": "When Claude Code runs a long heredoc or script with the Bash tool, nothing runs and it gets unexpected EOF while looking for matching, a quoting error, although the command has no quoting mistake. With text made mostly of single quotes, it happens at about 1,500 characters.",
        "why": "On Windows, Claude Code wraps the Bash tool command in setup and cleanup code and passes it as one bash.exe -c string. Git for Windows bash keeps only the first 8,186 characters of that string and drops the rest (official issue #102533). After the wrapper, about 7,400 characters are left for the command on the author's PC. According to the issue, each single quote is rewritten as five characters.",
        "fix": "Write long scripts and heredocs to a file with the Write tool, then run them with a short command such as bash script.sh. Say so in CLAUDE.md.",
        "fixcode": "# CLAUDE.md\n- On Windows, do not put long scripts or heredocs in Bash tool commands (the limit is in the 7,000s; a single quote counts as 5)\n- Write anything over a few thousand characters to a file with the Write tool and run bash <file>",
        "result": "with the Bash tool command replaced by a PreToolUse hook, 7,417 characters ran and 7,421 characters ran nothing; 1,450 single quotes (1,495 characters) ran and 1,500 (1,545 characters) did not; a 9,000-character body written to big.sh ran with bash big.sh (2026-11-25, Claude Code 2.1.330, Git for Windows 2.56.0)",
    },
})

TRAPS.append({
    "id": "h21",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\.claude" | Out-Null
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
if ($w) """ + YES,
    "ja": {
        "title": "フックの .ps1 が見つからないと、onFailure: block でも書き込みが通る",
        "search": ["onFailure block 効かない", "Claude Code フック ps1 見つからない", "0xFFFD0000", "-196608 PowerShell", "Claude Code hook onFailure block powershell -File"],
        "symptom": "書き込みを止めるフックを powershell.exe -File <スクリプト> で呼び、onFailure: block も付けていたのに、スクリプトを移したあとから書き込みが止まらない。エラーも出ない。",
        "why": "-File に渡した .ps1 が無いと、Windows PowerShell 5.1 は終了コード 0xFFFD0000（-196608）で終わる。Claude Code はこれを成功として扱い、onFailure: block が効かない（公式 issue #100891）。実行ファイルが無い・時間切れ・exit 1 なら止まる（issue による）。",
        "fix": "フックのコマンドの中でスクリプトがあるかを確かめ、無ければ exit 1 で終わらせる。最後に exit $LASTEXITCODE を書けば、スクリプトの exit 2 もそのまま返る。",
        "fixcode": "\"command\": \"powershell.exe\",\n\"args\": [\"-NoProfile\", \"-ExecutionPolicy\", \"Bypass\", \"-Command\", \"$s = 'C:/hooks/guard.ps1'; if (-not (Test-Path -LiteralPath $s -PathType Leaf)) { exit 1 }; $global:LASTEXITCODE = 0; & $s; if (-not $?) { if ($LASTEXITCODE) { exit $LASTEXITCODE } else { exit 1 } }; exit $LASTEXITCODE\"],\n\"onFailure\": \"block\"",
        "result": "-File の .ps1 を置かずに Write させると、out.txt ができ、デバッグの記録は success だった。直接流した終了コードは -196608。上の形にすると、無い・exit 2・構文の誤り・throw の4通りで止まり、exit 0 は通った（2026-11-25、Claude Code 2.1.330、Windows PowerShell 5.1）",
    },
    "en": {
        "title": "If a hook's .ps1 file is missing, writes go through even with onFailure: block",
        "search": ["onFailure block not blocking", "claude code hook ps1 missing", "0xFFFD0000", "-196608 powershell", "claude code hook onFailure block powershell -File"],
        "symptom": "A hook that blocks writes, called as powershell.exe -File <script> with onFailure: block, stops blocking after the script is moved or renamed. No error.",
        "why": "When the .ps1 passed to -File does not exist, Windows PowerShell 5.1 exits with 0xFFFD0000 (-196608). Claude Code treats that as success, so onFailure: block does not apply (official issue #100891). A missing executable, a timeout or exit 1 do block, per the issue.",
        "fix": "Check inside the hook command that the script exists and exit 1 if not. End with exit $LASTEXITCODE so a deny (exit 2) from the script still comes back as 2.",
        "fixcode": "\"command\": \"powershell.exe\",\n\"args\": [\"-NoProfile\", \"-ExecutionPolicy\", \"Bypass\", \"-Command\", \"$s = 'C:/hooks/guard.ps1'; if (-not (Test-Path -LiteralPath $s -PathType Leaf)) { exit 1 }; $global:LASTEXITCODE = 0; & $s; if (-not $?) { if ($LASTEXITCODE) { exit $LASTEXITCODE } else { exit 1 } }; exit $LASTEXITCODE\"],\n\"onFailure\": \"block\"",
        "result": "with the -File script left out, the Write went through (out.txt created) and the debug log said success; the same command run directly exited -196608; with the wrapper above, a missing script, exit 2, a syntax error and a throw all blocked, and exit 0 let the write through (2026-11-25, Claude Code 2.1.330, Windows PowerShell 5.1)",
    },
})

TRAPS.append({
    "id": "h16",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\Sub" | Out-Null
[IO.File]::WriteAllText("$d\Sub\EditBack.txt", "fruit = APPLE`r`n")
Push-Location $d
"First use the Read tool on the file Sub/EditBack.txt in the current folder. Then use the Edit tool exactly once with file_path set to exactly this string, character for character: $d\sub\editback.TXT . Replace APPLE with ORANGE. Use no other tools. Then stop." | claude -p --allowedTools "Read,Edit" | Out-Null
Pop-Location
$name = (Get-ChildItem -LiteralPath "$d\Sub" | ForEach-Object Name) -join ', '
$body = (Get-Content -LiteralPath "$d\Sub\EditBack.txt" -Raw).Trim()
"file name after the Edit: $name; content: $body"
if ($body -notmatch 'ORANGE') { 'CANNOT CHECK (the Edit did not happen: check that claude -p can use Read and Edit)' } elseif ($name -ceq 'editback.TXT') """ + YES,
    "ja": {
        "title": "Windows の Claude Code で Edit・Write すると、ファイル名の大文字小文字が黙って変わる",
        "search": ["Claude Code ファイル名 小文字になる", "Claude Code Edit ファイル名 変わる", "git status 大文字小文字 Windows 変わった", "core.ignorecase Claude Code", "Claude Code renames file case windows"],
        "symptom": "Claude Code に直させた Config.txt が、いつの間にか config.TXT のように大文字小文字の違う名前になっている。中身は正しく直っていて、ツールはいつもの「更新しました」としか言わない。Windows の git status には M としか出ない。",
        "why": "Edit・Write に渡したパス（file_path）の大文字小文字が実際の名前と違うと、Claude Code は中身を直したうえで、ファイル名を file_path の綴りに変える（公式 issue #100987）。PowerShell の Set-Content など、ふつうの書き込みでは名前は変わらない。Windows の git は大文字小文字を区別しない設定がふつうなので、名前の変化が見えない。",
        "fix": "Edit・Write の前に Glob や Read で実際の名前を確かめ、その綴りのまま file_path に書かせる。CLAUDE.md にもそう書く。commit の前に git -c core.ignorecase=false status --short で D と ?? の組が無いかを見る。",
        "fixcode": "git -c core.ignorecase=false status --short\n# D Config.txt と ?? config.TXT が並んでいたら、名前が変わっている",
        "result": "Read のあと Edit に ...\\sub\\editback.TXT を渡すと、EditBack.txt の中身が直り、名前が editback.TXT になった。/ 区切りでも Write でも同じ。Set-Content では Ctrl.txt のまま。git では M Config.txt としか出ず、core.ignorecase=false では D と ?? に分かれた（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "On Windows, Claude Code's Edit and Write silently change the letter case of the file name",
        "search": ["claude code renames file case windows", "claude code edit changes file name case", "git status case change windows claude", "core.ignorecase claude code edit", "claude code write lowercase filename"],
        "symptom": "A Config.txt that Claude Code edited is now called config.TXT or another spelling with different letter case. The content is correct, the tool only said it was updated, and git status on Windows shows just M.",
        "why": "When the file_path given to Edit or Write differs in letter case from the real name, Claude Code changes the content and also renames the file to the spelling in file_path (official issue #100987). Ordinary writes such as PowerShell Set-Content keep the name. Git on Windows ignores case by default, so the rename does not show.",
        "fix": "Have Claude check the real name with Glob or Read before Edit or Write and use that exact spelling in file_path; say so in CLAUDE.md. Before committing, run git -c core.ignorecase=false status --short and look for a D and ?? pair.",
        "fixcode": "git -c core.ignorecase=false status --short\n# a D Config.txt next to ?? config.TXT means the name changed",
        "result": "after Read, an Edit with file_path ...\\sub\\editback.TXT changed EditBack.txt's content and renamed it to editback.TXT; the same with forward slashes and with Write; Set-Content kept Ctrl.txt; git showed only M Config.txt, and with core.ignorecase=false it showed D and ?? (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "h23",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\.claude\hooks" | Out-Null
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
if (-not (Test-Path "$d\seen.txt")) { 'CANNOT CHECK (the hook did not run: check that python, git and Git for Windows bash are installed)' } elseif (-not $w) """ + YES,
    "ja": {
        "title": "Git Bash のフックで $PWD と file_path を比べると、Windows ではプロジェクトの中まで「外」になる",
        "search": ["Claude Code フック PWD file_path", "Claude Code hook outside the project Windows", "フック 全部 BLOCKED", "cygpath フック", "Claude Code bash hook path Windows"],
        "symptom": "Linux で動いていた「プロジェクトの外には書かせない」bash のフックが、Windows では中への書き込みまで全部止める。.claude/settings.json を直そうとしても止められる。",
        "why": "フックに届く tool_input.file_path は C:\\... の Windows の形。Git Bash の $PWD は /c/...・/tmp/...・C:/... の形で、文字のまま比べると先頭が一致しない（公式 issue #94256）。止める場所を書いた守りなら、逆に何も止めない。",
        "fix": "比べる両方を cygpath -u でそろえてから比べる。file_path だけでは足りない（$PWD が C:/... の形で来ることがある）。Python で書くなら、両方を os.path.realpath でそろえる。",
        "fixcode": "u() { cygpath -u \"$1\" 2>/dev/null || printf '%s' \"$1\"; }\nf=$(u \"$f\"); p=$(u \"$PWD\")\ncase \"$f\" in \"$p\"/*) exit 0;; *) echo \"BLOCKED\" >&2; exit 2;; esac",
        "result": "file_path は C:\\...\\out.txt、$PWD は回によって /tmp/... か C:/... の形で、プロジェクトの中への Write が止まった。両方を cygpath -u でそろえると、中は通り隣のフォルダは止まった（2026-11-25、Claude Code 2.1.330、Git for Windows）",
    },
    "en": {
        "title": "A Git Bash hook that compares $PWD with file_path treats even files inside the project as outside on Windows",
        "search": ["claude code hook PWD file_path windows", "claude code hook outside the project windows", "hook blocks every write windows", "cygpath claude code hook", "claude code bash hook path format"],
        "symptom": "A bash hook that keeps writes inside the project works on Linux but on Windows blocks every write, including writes inside the project and edits to .claude/settings.json.",
        "why": "tool_input.file_path arrives in Windows form (C:\\...). Git Bash's $PWD is /c/..., /tmp/... or C:/..., so a plain string prefix never matches (official issue #94256). A deny-list hook written the same way blocks nothing.",
        "fix": "Normalize both sides with cygpath -u before comparing. Normalizing only file_path is not enough, because $PWD can come as C:/....",
        "fixcode": "u() { cygpath -u \"$1\" 2>/dev/null || printf '%s' \"$1\"; }\nf=$(u \"$f\"); p=$(u \"$PWD\")\ncase \"$f\" in \"$p\"/*) exit 0;; *) echo \"BLOCKED\" >&2; exit 2;; esac",
        "result": "file_path was C:\\...\\out.txt and $PWD was /tmp/... or C:/... depending on the run, and a Write inside the project was blocked; with both sides passed through cygpath -u, a Write inside went through and a Write to a sibling folder was blocked (2026-11-25, Claude Code 2.1.330, Git for Windows)",
    },
})

TRAPS.append({
    "id": "h18",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\sub" | Out-Null
[IO.File]::WriteAllText("$d\sub\CLAUDE.md", "# Rules for this folder`nWhenever you answer after reading a file in this folder, end your answer with the code word ZEBRA-42.`n")
[IO.File]::WriteAllText("$d\sub\a.txt", "hello`n")
Set-Location $d
$lower = 'c' + $d.Substring(1)
$got = @()
foreach ($p in "$d\sub\a.txt", "$lower\sub\a.txt") {
    $ans = "Use the Read tool once with file_path set to exactly this string: $p . Then reply with the file's content and follow any instructions you were given for that folder." | claude -p --allowedTools Read | Out-String
    $got += ($ans -match 'ZEBRA-42')
}
"sub\CLAUDE.md applied with C:\ path: $($got[0]); with c:\ path: $($got[1])"
if ($d.Substring(0, 2) -ne 'C:') { 'CANNOT CHECK (TEMP is not on drive C:)' } elseif (-not $got[0]) { 'CANNOT CHECK (the folder CLAUDE.md was not applied even with C:\: check that claude -p can use Read)' } elseif (-not $got[1]) """ + YES,
    "ja": {
        "title": "Windows の Claude Code は、パスのドライブ文字が小文字（c:\\）だと、下のフォルダの CLAUDE.md を読まない",
        "search": ["Claude Code CLAUDE.md 読まれない サブフォルダ", "Claude Code nested CLAUDE.md not loaded windows", "Claude Code ドライブ文字 小文字", "c:\\ C:\\ Claude Code CLAUDE.md", "Claude Code フォルダごとの CLAUDE.md 効かない"],
        "symptom": "下のフォルダに置いた CLAUDE.md の決まりを、Claude Code がときどき守らない。守らなかった回は、Read に渡したパスのドライブ文字の大小が、起動したフォルダと違っていた（C: で起動して c:\\ で読んだ、など）。エラーも警告も出ない。",
        "why": "Claude Code は、下のフォルダのファイルを Read したときにそのフォルダの CLAUDE.md を読み込むが、Windows ではドライブ文字の大小が起動したフォルダと違うと読み込まない（公式 issue #98835。報告は VS Code で c:\\ として開いたワークスペースで C:\\ が読まれなかった、作者は C: で起動して c:\\ が読まれなかった）。",
        "fix": "必ず守らせたい決まりは、起動するフォルダの CLAUDE.md に書く（起動したフォルダのものは最初に読まれる）。CLAUDE.md に「パスはドライブ文字を大文字で C:/ と書く」と書く。",
        "fixcode": "# CLAUDE.md\n- Windows のパスは、ドライブ文字を大文字で C:/ と書き、/ 区切りにする",
        "result": "C: で起動した claude -p で、Read の file_path が C:\\ と C:/ なら sub\\CLAUDE.md が効き、c:\\ と c:/ では効かなかった（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "On Windows, Claude Code skips a subfolder's CLAUDE.md when the path's drive letter is lowercase (c:\\)",
        "search": ["claude code nested CLAUDE.md not loaded windows", "claude code subdirectory CLAUDE.md ignored", "claude code drive letter case c: C:", "claude code CLAUDE.md lowercase drive letter", "claude code folder rules not applied windows"],
        "symptom": "Claude Code sometimes ignores the rules in a CLAUDE.md placed in a subfolder. In those runs, the drive letter in the path given to Read differed in case from the folder Claude Code started in (started in C:, read with c:\\). No error, no warning.",
        "why": "Claude Code loads a subfolder's CLAUDE.md when it reads a file there, but on Windows it does not when the drive letter's case differs from the starting folder (official issue #98835: the report had a VS Code workspace opened as c:\\ with C:\\ reads failing; the author started in C: and c:\\ reads failed).",
        "fix": "Put rules that must always apply in the CLAUDE.md of the folder Claude Code starts in (that one is loaded at startup). Tell Claude in CLAUDE.md to write paths with an uppercase drive letter, C:/.",
        "fixcode": "# CLAUDE.md\n- On Windows, write paths with an uppercase drive letter (C:/) and forward slashes",
        "result": "in claude -p started in C:, the subfolder CLAUDE.md applied when Read got C:\\ or C:/ and did not when it got c:\\ or c:/ (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "h20",
    "claude": True,
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\s.json", '{"env":{"CLAUDE_CODE_USE_POWERSHELL_TOOL":"1"}}')
Push-Location $d
$out = "You must use the PowerShell tool (not Bash). Run exactly the PowerShell command in the next line once, then stop.`ncmd /c exit 3; 'done'" | claude -p --settings s.json --allowedTools PowerShell --output-format stream-json --verbose | Out-String
Pop-Location
$ran = $out -match 'done'
$err = $out -match '"is_error":true'
"the PowerShell tool ran the command: $ran; the call was reported as an error: $err"
if (-not $ran) { 'CANNOT CHECK (the PowerShell tool did not run: check that claude -p can use it)' } elseif ($err -and ($out -match 'Exit code 3')) """ + YES,
    "ja": {
        "title": "Claude Code の PowerShell ツールは、途中のコマンドの終了コードで、成功を「失敗」と返す",
        "search": ["Claude Code PowerShell Exit code 1 robocopy", "Claude Code PowerShell ツール 失敗 成功してるのに", "LASTEXITCODE Claude Code", "Claude Code PowerShell tool exit code wrong", "robocopy exit code 1 Claude Code"],
        "symptom": "Claude Code が PowerShell ツールで robocopy などを動かすと、コピーはできているのに Exit code 1 の失敗として返り、Claude がやり直したり、コマンドを書き換えたりする。最後の文は成功している。",
        "why": "PowerShell では、外のプログラムの終了コードが $LASTEXITCODE に残る。PowerShell ツールは、最後に残った $LASTEXITCODE を呼び出し全体の結果として返す（公式 issue #97589）。ふつうの powershell -Command や -File では、同じコマンドの終了コードは 0 になる。robocopy は成功でも 1〜7 を返す。",
        "fix": "成功でも 0 以外を返すコマンド（robocopy・findstr・git diff --quiet など）のあとは、終わりに exit 0 を付け、終了コードは文字で出す。本当の失敗も失敗扱いにならなくなるので、出した exit= の行を読ませる。",
        "fixcode": "robocopy src dst a.txt | Out-Null; $rc = $LASTEXITCODE; if ($rc) { \"exit=$rc\" }; exit 0",
        "result": "PowerShell ツールで cmd /c exit 3; 'done' は done まで動いたのに is_error=true・Exit code 3。robocopy で1つコピーしても Exit code 1 の失敗（コピーはできていた）。; exit 0 を足すと失敗にならない。ふつうの powershell -Command と -File では 0（2026-11-25、Claude Code 2.1.330、Windows PowerShell 5.1）",
    },
    "en": {
        "title": "Claude Code's PowerShell tool reports success as failure because of an earlier command's exit code",
        "search": ["claude code powershell exit code 1 robocopy", "claude code powershell tool reports failure but succeeded", "LASTEXITCODE claude code powershell tool", "claude code powershell tool exit code wrong", "robocopy exit code 1 claude code"],
        "symptom": "When Claude Code runs robocopy or similar in the PowerShell tool, the copy works but the call comes back as a failure with Exit code 1, and Claude retries or rewrites the command. The last statement succeeded.",
        "why": "In PowerShell an external program's exit code stays in $LASTEXITCODE. The PowerShell tool returns whatever $LASTEXITCODE holds at the end as the result of the whole call (official issue #97589). Plain powershell -Command or -File gives 0 for the same command. robocopy returns 1-7 on success.",
        "fix": "After commands that return non-zero on success (robocopy, findstr, git diff --quiet), end with exit 0 and print the exit code as text. Real failures are then not flagged either, so have Claude read the exit= line.",
        "fixcode": "robocopy src dst a.txt | Out-Null; $rc = $LASTEXITCODE; if ($rc) { \"exit=$rc\" }; exit 0",
        "result": "in the PowerShell tool, cmd /c exit 3; 'done' printed done but came back as is_error=true, Exit code 3; copying one file with robocopy came back as Exit code 1 although the copy worked; adding ; exit 0 removed the error; plain powershell -Command and -File gave 0 (2026-11-25, Claude Code 2.1.330, Windows PowerShell 5.1)",
    },
})

TRAPS.append({
    "id": "h22",
    "claude": True,
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\case.txt", "a`tb`tc`n1`t2`t3`n")
Push-Location $d
"Use the Read tool on case.txt, then use the Edit tool once on case.txt with old_string set to exactly one TAB character, new_string set to exactly two space characters, and replace_all true. Use no other tools. Then stop." | claude -p --allowedTools "Read,Edit" | Out-Null
Pop-Location
$b = [IO.File]::ReadAllBytes("$d\case.txt")
"case.txt was 12 bytes with 4 tabs; asked to turn each tab into two spaces; now $($b.Length) bytes, tabs left: $(@($b | Where-Object { $_ -eq 9 }).Count)"
if ($b.Length -eq 12) { 'CANNOT CHECK (the Edit did not happen: check that claude -p can use Read and Edit)' } elseif ($b.Length -eq 8) """ + YES,
    "ja": {
        "title": "Claude Code の Edit・Write は、.md 以外のファイルで行末の空白を黙って消す（タブを空白に置き換えると、消えるだけ）",
        "search": ["Claude Code タブ 空白 置き換え 消える", "Claude Code Edit 行末 空白 消える", "Claude Code trailing whitespace removed", "Claude Code Write 空白 消える txt", "Claude Code インデント 消えた"],
        "symptom": "Claude Code にタブを空白に揃えさせたら、タブが消えただけで空白が入っていない（a<TAB>b が ab になる）。ツールは置き換えが済んだと返す。Write で書いたファイルも、行末の空白が消えている。.md のファイルでは起きない。",
        "why": "Edit と Write は、.md 以外のファイルでは、渡された文字列の各行の末尾の空白（空白とタブ）を取り除いてから書く（公式 issue #100296）。置き換え先が空白だけだと全部が行末の空白とみなされて空になり、置き換えが削除になる。",
        "fix": "空白だけの置き換えや、行末の空白を残したい書き込みは、Edit・Write ではなくスクリプト（PowerShell の -replace や Python）でやらせ、終わったらバイト数や git diff で確かめる。CLAUDE.md にもそう書く。",
        "fixcode": "$t = [IO.File]::ReadAllText('C:/work/case.txt')\n[IO.File]::WriteAllText('C:/work/case.txt', $t.Replace(\"`t\", '  '))",
        "result": ".txt でタブ1つを空白2つに Edit（replace_all）すると、タブが消えて空白は入らず 12→8 バイト。.md では空白2つが入った。Write も .txt では行末の空白が消え、.md では残った（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "Claude Code's Edit and Write silently strip trailing whitespace outside .md files (tabs-to-spaces just deletes the tabs)",
        "search": ["claude code edit tabs to spaces deletes tabs", "claude code trailing whitespace removed", "claude code write strips trailing spaces", "claude code edit whitespace only new_string", "claude code indentation lost"],
        "symptom": "You ask Claude Code to turn tabs into spaces and the tabs are gone with no spaces in their place (a<TAB>b becomes ab), while the tool says the replacement was made. Files written with Write lose their trailing spaces too. .md files are not affected.",
        "why": "Outside .md files, Edit and Write strip whitespace at the end of each line of the text they are given before writing (official issue #100296). A replacement made only of whitespace is all trailing, so it becomes empty and the replacement turns into a deletion.",
        "fix": "Do whitespace-only replacements, and writes that must keep trailing spaces, with a script (PowerShell -replace or Python) instead of Edit or Write, then check the byte count or git diff. Say so in CLAUDE.md.",
        "fixcode": "$t = [IO.File]::ReadAllText('C:/work/case.txt')\n[IO.File]::WriteAllText('C:/work/case.txt', $t.Replace(\"`t\", '  '))",
        "result": "an Edit with replace_all turning one tab into two spaces in a .txt file deleted the tabs and wrote no spaces (12 to 8 bytes); in a .md file the spaces were written; Write also dropped trailing spaces in .txt and kept them in .md (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "h24",
    "claude": True,
    "check": HEAD + r"""New-Item -ItemType Directory -Force "$d\a\b\sub" | Out-Null
[IO.File]::WriteAllText("$d\a\b\sub\SKILL.md", "markerterm`n")
Push-Location $d
$found = @()
foreach ($g in '**/SKILL.md', '*/SKILL.md') {
    $out = "Use the Grep tool exactly once with pattern set to markerterm, path set to exactly $d\a\b , glob set to exactly $g , and output_mode files_with_matches. Use no other tools. Then stop." | claude -p --allowedTools Grep --output-format stream-json --verbose | Out-String
    $found += ($out -match 'Found 1 file')
}
Pop-Location
"glob **/SKILL.md found the file: $($found[0]); glob */SKILL.md found the file: $($found[1])"
if (-not $found[0]) { 'CANNOT CHECK (even **/SKILL.md found nothing: check that claude -p can use Grep)' } elseif (-not $found[1]) """ + YES,
    "ja": {
        "title": "Claude Code の Grep は、作業フォルダの下を探すとき、glob の */ が「見つからない」になる",
        "search": ["Claude Code Grep No files found あるのに", "Claude Code Grep glob 見つからない", "Claude Code Grep glob */ path", "claude code grep glob relative working directory", "Claude Code 検索 見つからない ファイルはある"],
        "symptom": "Claude Code が Grep で探して No files found と返し、「そのファイルはありません」と判断する。実際にはファイルがある。探す範囲（path）を作業フォルダの下にして、glob に */ を使っていた。",
        "why": "Grep の glob は、path からではなく作業フォルダからの相対パスで照らし合わされる（公式 issue #104991）。path が a\\b でも sub\\SKILL.md は a/b/sub/SKILL.md として照らされるので、1段だけの */SKILL.md には当たらない。**/ はどの深さにも当たる。",
        "fix": "glob は **/ で書く。CLAUDE.md にもそう書き、No files found のときは glob を外して探し直させる。",
        "fixcode": "# CLAUDE.md\n- Grep の glob は作業フォルダからの相対で照らされる。*/ ではなく **/ で書く\n- No files found のときは、glob を外してもう一度探す",
        "result": "作業フォルダの下の a\\b を path にした Grep で、glob */SKILL.md は No files found、**/SKILL.md と a/b/*/SKILL.md は a\\b\\sub\\SKILL.md を見つけた（2026-11-25、Claude Code 2.1.330、Windows 11）",
    },
    "en": {
        "title": "Claude Code's Grep returns No files found for a */ glob when searching below the working folder",
        "search": ["claude code grep no files found but file exists", "claude code grep glob not matching", "claude code grep glob path relative", "claude code grep glob relative to working directory", "claude code grep one level glob"],
        "symptom": "Claude Code searches with Grep, gets No files found, and concludes the file does not exist, although it does. The search path was below the working folder and the glob used */.",
        "why": "Grep matches the glob against the path relative to the working folder, not relative to the path argument (official issue #104991). With path a\\b, sub\\SKILL.md is matched as a/b/sub/SKILL.md, so a one-level */SKILL.md does not match. **/ matches at any depth.",
        "fix": "Write globs with **/. Say so in CLAUDE.md, and have Claude search again without the glob when it gets No files found.",
        "fixcode": "# CLAUDE.md\n- Grep globs are matched relative to the working folder. Use **/ instead of */\n- On No files found, search again without the glob",
        "result": "with path a\\b below the working folder, glob */SKILL.md gave No files found, while **/SKILL.md and a/b/*/SKILL.md found a\\b\\sub\\SKILL.md (2026-11-25, Claude Code 2.1.330, Windows 11)",
    },
})

TRAPS.append({
    "id": "c01",
    "check": HEAD + r"""[IO.File]::WriteAllText("$d\hex.py", 'import sys; print(sys.stdin.buffer.read().strip().hex())')
$s = 'Zo' + [char]0xE9 + ' ' + [char]0x65E5 + [char]0x672C
$h = $s | python "$d\hex.py"
"bytes=$h  (UTF-8 would be 5a6fc3a920e697a5e69cac)"
if ($h -match '3f') """ + YES,
    "ja": {
        "title": "Codex CLI が PowerShell 5.1 でパイプに渡した日本語が ? になる（終了コード 0）",
        "search": ["Codex CLI 文字化け ?", "Codex CLI Windows 日本語 パイプ", "codex exec powershell 文字化け", "Codex PowerShell 5.1 OutputEncoding", "codex windows non-ascii pipe question mark"],
        "symptom": "Codex CLI に、日本語を含む文字列を python などのコマンドへパイプで渡させると、受け取った側には ? が届く。コマンドは終了コード 0 で終わり、Codex も化けに気づかずにそのまま答える。PowerShell 7 が無い Windows で、Codex が Windows PowerShell 5.1 でコマンドを動かすときに起きる。",
        "why": "PowerShell 7 が無いと、Codex は powershell.exe（5.1）の -Command でコマンドを動かす。5.1 は外部のコマンドに渡す文字を $OutputEncoding で符号化し、その既定が ASCII なので、ASCII にない文字はすべて ? になる（公式 issue openai/codex #64139）。T04 と同じ仕組み。",
        "fix": "パイプの前に $OutputEncoding を UTF-8 にする。Codex に任せるなら、プロジェクトの AGENTS.md に「パイプの前に $OutputEncoding を UTF-8 にする」と書く（効きやすくなるが、確実ではない）。",
        "fixcode": "$OutputEncoding = [Text.UTF8Encoding]::new($false)\n'Zoé 日本' | python -c \"import sys; print(sys.stdin.buffer.read().hex())\"",
        "result": "既定では 5a6f3f203f3f（Zo? ??）、$OutputEncoding を UTF-8 にすると 5a6fc3a920e697a5e69cac（2026-11-27、codex-cli 0.167.0-alpha.3.2、Windows PowerShell 5.1.26100、PowerShell 7 なし）",
    },
    "en": {
        "title": "Codex CLI on PowerShell 5.1: non-ASCII text piped to a command arrives as ? (exit code 0)",
        "search": ["codex cli windows question marks pipe", "codex exec powershell non-ascii", "codex powershell 5.1 OutputEncoding", "codex windows unicode pipe broken", "openai codex windows mojibake"],
        "symptom": "When Codex CLI pipes text with non-ASCII characters into a command such as python, the command receives ? instead. The command exits 0 and Codex does not notice. This happens on Windows without PowerShell 7, where Codex runs commands in Windows PowerShell 5.1.",
        "why": "Without PowerShell 7, Codex runs commands with powershell.exe (5.1) -Command. PowerShell 5.1 encodes text sent to external commands with $OutputEncoding, which defaults to ASCII, so every non-ASCII character becomes ? (official issue openai/codex #64139). Same mechanism as T04.",
        "fix": "Set $OutputEncoding to UTF-8 before piping. To have Codex do it, write the rule in the project's AGENTS.md (it helps but is not guaranteed).",
        "fixcode": "$OutputEncoding = [Text.UTF8Encoding]::new($false)\n'Zoé 日本' | python -c \"import sys; print(sys.stdin.buffer.read().hex())\"",
        "result": "default gave 5a6f3f203f3f (Zo? ??); with $OutputEncoding set to UTF-8, 5a6fc3a920e697a5e69cac (2026-11-27, codex-cli 0.167.0-alpha.3.2, Windows PowerShell 5.1.26100, no PowerShell 7)",
    },
})

TRAPS.append({
    "id": "c02",
    "check": HEAD + r"""$s = [string][char]0x65E5 + [char]0x672C + [char]0x8A9E
[IO.File]::WriteAllText("$d\note.md", $s, [Text.UTF8Encoding]::new($false))
$a = Get-Content -LiteralPath "$d\note.md"
$b = Get-Content -LiteralPath "$d\note.md" -Encoding UTF8
"default read equals the file: $($a -eq $s); with -Encoding UTF8: $($b -eq $s)"
if ($a -ne $s -and $b -eq $s) """ + YES,
    "ja": {
        "title": "Codex CLI が PowerShell 5.1 で読んだ UTF-8（BOM なし）の日本語が化ける（終了コード 0）",
        "search": ["Codex CLI 文字化け Get-Content", "Codex CLI Windows 日本語 化ける", "codex 繝 文字化け", "Codex PowerShell 5.1 UTF-8 BOM なし", "codex windows utf-8 without bom mojibake"],
        "symptom": "Codex CLI に、BOM なしの UTF-8 で保存した日本語のファイル（Markdown など）を読ませると、「繝｡繝｢」のような化けた文字で読む。終了コードは 0 で、Codex は化けたまま「そのまま写した」と答える。",
        "why": "PowerShell 7 が無いと、Codex は Windows PowerShell 5.1 の Get-Content でファイルを読む。5.1 は BOM の無いファイルを、日本語の Windows では cp932（Shift_JIS）として読むので、UTF-8 の日本語が化ける（公式 issue openai/codex #29085。報告はトルコ語だが日本語でも起きる）。",
        "fix": "読むときに -Encoding UTF8 を付ける。Codex に任せるなら、プロジェクトの AGENTS.md に「Get-Content は -Encoding UTF8 で」と書く（効きやすくなるが、確実ではない）。",
        "fixcode": "Get-Content -Encoding UTF8 note.md",
        "result": "既定の Get-Content は化けた（「メモ」が「繝｡繝｢」に）、-Encoding UTF8 は元のとおり（2026-11-27、codex-cli 0.167.0-alpha.3.2、Windows PowerShell 5.1.26100、コードページ 932）",
    },
    "en": {
        "title": "Codex CLI on PowerShell 5.1 misreads UTF-8 (no BOM) Japanese files (exit code 0)",
        "search": ["codex cli windows utf-8 mojibake", "codex Get-Content encoding", "codex powershell 5.1 utf-8 without bom", "codex windows non-ascii file garbled", "openai codex windows encoding"],
        "symptom": "When Codex CLI reads a UTF-8 file without a BOM that contains Japanese (Markdown, for example), it gets garbled characters such as 繝｡繝｢. The command exits 0 and Codex reports that it copied the text as is.",
        "why": "Without PowerShell 7, Codex reads files with Get-Content in Windows PowerShell 5.1. On Japanese Windows, 5.1 reads a file without a BOM as cp932 (Shift_JIS), so UTF-8 Japanese is garbled (official issue openai/codex #29085; reported for Turkish, also happens with Japanese).",
        "fix": "Add -Encoding UTF8 when reading. To have Codex do it, write the rule in the project's AGENTS.md (it helps but is not guaranteed).",
        "fixcode": "Get-Content -Encoding UTF8 note.md",
        "result": "the default Get-Content garbled the text, -Encoding UTF8 read it correctly (2026-11-27, codex-cli 0.167.0-alpha.3.2, Windows PowerShell 5.1.26100, code page 932)",
    },
})

PY_IDS = PY_IDS + ("c01",)

# wrap every check that needs python in the guard (HEAD stays outside)
for _tr in TRAPS:
    if _tr["id"] in PY_IDS:
        _body = _tr["check"][len(HEAD):]
        _tr["check"] = HEAD + PY_GUARD + _body + "\n}"
