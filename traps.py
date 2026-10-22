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
            "title": "-File で渡した2つ目の引数が、エラーなしで消える",
            "search": ["powershell -File 配列 引数 渡せない", "string[] 引数 1つしか入らない", "powershell 引数 消える"],
            "symptom": "[string[]] の引数に -Path a b と2つ渡したのに、スクリプトには a しか入っていない。エラーも出ず、終了コードも 0。",
            "why": "-File で呼ぶと、引数は文字列のまま1つずつ渡る。-Path に入るのは a だけで、b はどの引数にも当たらない余りとして $args に回り、そのまま捨てられる。",
            "fix": "param の前に [CmdletBinding()] を付ける。余った引数があるとエラーで止まるようになる。複数の値は1つの文字列で受けて、自分で分ける（次の T03）。",
            "fixcode": "[CmdletBinding()]\nparam([string]$Path)\n$paths = $Path -split ','",
            "result": "count=1 first=a、終了コード 0（[CmdletBinding()] を付けると終了コード 1 で止まった）",
        },
        "en": {
            "title": "The second value passed with -File disappears without an error",
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
            "title": "-File で a,b と渡すと、配列にならず1つの文字列になる",
            "search": ["powershell -File カンマ 配列にならない", "a,b 1つのパス", "指定されたパスが見つかりません カンマ"],
            "symptom": "-Path a,b と書けば2つのパスになるつもりが、a,b という名前のパス1つとして扱われ、「見つからない」になるか、黙って何もしない。",
            "why": "-File で渡した引数は PowerShell の式として解釈されない。カンマで配列を作るのは、PowerShell の中で呼んだときだけ。",
            "fix": "1つの文字列で受けて、スクリプトの中で -split ',' で分ける。",
            "fixcode": "param([string]$Path)\nforeach ($p in ($Path -split ',')) { $p.Trim() }",
            "result": "count=1 first=a,b",
        },
        "en": {
            "title": "With -File, a,b stays one string instead of an array",
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
if ($h -match '^(3f)+$') """ + YES,
        "ja": {
            "title": "パイプで渡した日本語が ? になる（claude -p・python・git）",
            "search": ["PowerShell パイプ 日本語 ?になる", "claude -p 日本語 文字化け", "python stdin 日本語 ??", "$OutputEncoding"],
            "symptom": "PowerShell から \"日本語\" | claude -p のように渡すと、相手には ?? が届く。エラーは出ない。Claude なら「文字化けしていたので推測した」と言いながら、指示と違うことをする。",
            "why": "Windows PowerShell 5.1 は、ネイティブのプログラムへパイプで渡す文字を $OutputEncoding で符号化する。既定は ASCII なので、日本語は ? になる。受け取る側の [Console]::OutputEncoding とは別の設定。",
            "fix": "長い日本語は UTF-8 のファイルに書き、ASCII だけの指示で「このファイルを読んで」と渡す。保険として $OutputEncoding を UTF-8 にする。",
            "fixcode": "$OutputEncoding = New-Object System.Text.UTF8Encoding $false\n'Read C:/work/prompt.md and do exactly what it says.' | claude -p",
            "result": "バイト 3f3f（? が2つ）",
        },
        "en": {
            "title": "Non-ASCII text piped to claude -p, python or git arrives as ?",
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
            "title": "python や claude の出力を変数に入れると文字化けする",
            "search": ["PowerShell 出力 文字化け 変数", "譌･譛ｬ", "python 出力 文字化け PowerShell", "Console OutputEncoding"],
            "symptom": "画面に直接出すと読めるのに、$x = python ... で受け取ると「譌･譛ｬ」のような文字になる。ログに書くと、そのまま化けて残る。",
            "why": "PowerShell はネイティブのプログラムの出力を [Console]::OutputEncoding（日本語の Windows では既定 932）で読む。相手が UTF-8 で書いていると、読み違える。",
            "fix": "出力を読む側で [Console]::OutputEncoding を UTF-8 にする。送る側の Python は PYTHONIOENCODING を utf-8 に（次の T06）。両方そろえる。",
            "fixcode": "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n$env:PYTHONIOENCODING = 'utf-8'",
            "result": "2文字が別の4文字になった",
        },
        "en": {
            "title": "Output from python or claude turns into mojibake in a variable",
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
            "title": "手で動かすと通る Python が、タスクスケジューラやリダイレクトのときだけ落ちる",
            "search": ["UnicodeEncodeError cp932", "タスクスケジューラ python 動かない", "python リダイレクト エラー", "'cp932' codec can't encode character"],
            "symptom": "画面で動かすと通るスクリプトが、> ファイル へのリダイレクトやタスクスケジューラ経由のときだけ UnicodeEncodeError で落ちる。— や ✓ のような記号を print しただけで起きる。",
            "why": "Windows の Python は、出力先が画面なら Unicode をそのまま書けるが、ファイルやパイプだと既定のコードページ（日本語なら cp932）で符号化する。その表に無い文字で落ちる。なお Python 3.15（2026年10月9日公開）は UTF-8 を既定にしたので（PEP 686）、3.15 以降では起きない見込み（作者の PC は 3.13.7 で、3.15 では試していない。確かめるコードは最初に Python の版を出す）。",
            "fix": "送る側で PYTHONIOENCODING=utf-8 を設定する。アプリで直すなら、画面でないときだけ sys.stdout.reconfigure(encoding='utf-8')。",
            "fixcode": "$env:PYTHONIOENCODING = 'utf-8'",
            "result": "UnicodeEncodeError、終了コード 1",
        },
        "en": {
            "title": "Python works when run by hand but crashes under Task Scheduler or redirection",
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
            "title": "日本語入りの .ps1 が、構文エラーになるか文字化けして動く",
            "search": ["ps1 日本語 文字化け", "ps1 BOM 必要", "PowerShell 5.1 UTF-8 構文エラー", "式またはステートメントのトークン"],
            "symptom": "エディタでは正しく見える .ps1 が、実行すると「文字列に終端記号がありません」などの構文エラーになるか、エラーなしで化けた文字を出す。",
            "why": "Windows PowerShell 5.1 は、BOM の無い .ps1 を UTF-8 ではなく ANSI コードページ（日本語なら 932）として読む。今のエディタの多くは BOM なしの UTF-8 で保存する。",
            "fix": "日本語を含む .ps1 は UTF-8（BOM 付き）で保存する。または .ps1 を ASCII だけで書き、日本語は [char]0x65E5 のように組み立てる。",
            "fixcode": "$t = [IO.File]::ReadAllText($path)\n[IO.File]::WriteAllText($path, $t, (New-Object System.Text.UTF8Encoding $true))",
            "result": "出力が元と違った",
        },
        "en": {
            "title": "A .ps1 with non-ASCII text fails to parse or prints mojibake",
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
            "title": "\"...\" に書いた Markdown のバッククォートで、文字が消えて改行が入る",
            "search": ["PowerShell バッククォート 消える", "ヒアストリング Markdown 文字化け", "PowerShell `n 改行 勝手に"],
            "symptom": "\"...\" や @\"...\"@ に `night-shift` のようなコード表記を書くと、n が消えて改行になる。`true` なら t が消えてタブ。エラーは出ず、ファイルの一部が欠けるだけ。",
            "why": "バッククォートは PowerShell のエスケープ文字。`n は改行、`t はタブ、`0 は NUL として解釈される。",
            "fix": "バッククォートを含む文章は単一引用符のヒアストリング @'...'@ に書き、差し込みは .Replace() で行う。書いたら出力を読み返す。",
            "fixcode": "$tpl = @'\nuse `night-shift` and `NAME`.\n'@\n$text = $tpl.Replace('NAME', $name)",
            "result": "改行が入った",
        },
        "en": {
            "title": "Markdown backticks inside \"...\" turn into newlines and tabs",
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
            "title": "書き込み中のログが 0 バイトに見える",
            "search": ["ログ 0バイト 書き込み中", "Get-ChildItem Length 0 なのに", "ファイルサイズ 更新されない Windows"],
            "symptom": "常駐プロセスが書いているログを Get-ChildItem で見ると 0 バイト。「何も出ていない」と判断したら、実際は数 MB 書かれていた。",
            "why": "Windows は、開いたまま書き続けているファイルの一覧上のサイズを、すぐには更新しないことがある（作者の PC では AppData の下で再現）。",
            "fix": "空かどうかを判断する前に、ファイルを開いて長さを読む。",
            "fixcode": "$fs = [IO.File]::Open($log, 'Open', 'Read', 'ReadWrite')\n$fs.Length; $fs.Close()",
            "result": "一覧では 0、実際は 5,000,000 バイト",
        },
        "en": {
            "title": "A log that is being written shows 0 bytes",
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
            "title": "Claude Code の PreToolUse フックが、時間切れになると書き込みを止めずに通す",
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

# wrap every check that needs python in the guard (HEAD stays outside)
for _tr in TRAPS:
    if _tr["id"] in PY_IDS:
        _body = _tr["check"][len(HEAD):]
        _tr["check"] = HEAD + PY_GUARD + _body + "\n}"
