"""Build the static site into docs/ (GitHub Pages serves this folder) and the check scripts into checks/.
    python build.py
Everything comes from traps.py. Do not edit docs/ by hand.
"""
import html
import pathlib
import shutil

from traps import AUTHOR_ENV, TRAPS

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
CHECKS = ROOT / "checks"
# Assumed GitHub Pages address; change here if the repository lives elsewhere.
BASE = "https://cart231-ffly-b.github.io/cc-win-symptoms/"
TRAPS_REPO = "https://github.com/cart231-ffly-b/claude-code-windows-traps"

LINKS = {
    "ja": {
        "free_t": ("エラーなしで壊れる14か所（無料の記事）", "https://note.com/sodateru_ai/n/na7d9ee2a36fa"),
        "free_h": ("安全フックは、遅れると黙って素通りする（無料の記事）", "https://note.com/sodateru_ai/n/n17e499f58486"),
        "kit": ("cc-win-kit（note、2,980円）", "https://note.com/sodateru_ai/n/ndad0eb6feaa6"),
        "repo": ("14か所をまとめて試すスクリプト cc-win-traps（無料、MIT）", TRAPS_REPO),
    },
    "en": {
        "free_t": ("cc-win-traps: run all 14 checks at once (free, MIT)", TRAPS_REPO),
        "free_h": ("cc-win-traps: run all 14 checks at once (free, MIT)", TRAPS_REPO),
        "kit": ("cc-win-kit ($19 on Payhip)", "https://payhip.com/b/bRnDJ"),
        "repo": None,
    },
}

T = {
    "ja": {
        "site": "Windows で Claude Code が黙って壊れるとき",
        "lead": "エラーは出ないのに、結果だけが違う。Windows で Claude Code やスクリプトを自動で回すと出会う症状を、1つずつ「30秒で確かめる → 原因 → 直し方」でまとめました。どれも作者の PC で実際に起きたものです。",
        "symptom": "症状",
        "check": "30秒で確かめる",
        "check_note": "PowerShell（Windows PowerShell 5.1）に貼って実行します。一時フォルダ（%TEMP% の下）にだけファイルを作ります。最後に REPRODUCED と出たら、あなたの PC で起きています。",
        "check_claude": "claude を1回呼ぶので、1分ほどかかります。",
        "check_slow": "25秒ほどかかります。",
        "why": "なぜ起きるか",
        "fix": "直し方",
        "result": "作者の PC での結果",
        "search": "こんな言葉で探した人へ",
        "more": "ほかの症状",
        "related": "関連",
        "kit": "この穴を最初から踏まないようにした部品（書き込み先を絞る安全装置〈onFailure: block 付き〉、夜の無人実行、ファイルとフックの設定を調べる健康診断、CLAUDE.md の型、試験一式）は cc-win-kit にまとめています。",
        "copy": "コピー",
        "copied": "コピーしました",
        "other": "English",
        "index": "一覧へ",
        "hooks": "Claude Code のフック",
        "ps": "PowerShell・Python・cmd",
        "footer": "作者: 上条碧斗（Kamijo Aoto）。内容は作者の PC で確かめた範囲です。",
    },
    "en": {
        "site": "When Claude Code breaks silently on Windows",
        "lead": "No error, just a wrong result. Each page takes one symptom you meet when running Claude Code or scripts unattended on Windows: a 30-second check, the cause and the fix. Every one happened on the author's machine.",
        "symptom": "Symptom",
        "check": "Check it in 30 seconds",
        "check_note": "Paste into Windows PowerShell 5.1. It only creates files under your %TEMP% folder. If the last line says REPRODUCED, it happens on your machine.",
        "check_claude": "It calls claude once, so it takes about a minute.",
        "check_slow": "It takes about 25 seconds.",
        "why": "Why it happens",
        "fix": "Fix",
        "result": "On the author's machine",
        "search": "If you searched for",
        "more": "Other symptoms",
        "related": "Related",
        "kit": "cc-win-kit bundles the parts that avoid these traps from the start: a write guard (with onFailure: block), an unattended runner, a doctor that scans your files and hook settings, CLAUDE.md templates and the full test suite.",
        "copy": "Copy",
        "copied": "Copied",
        "other": "日本語",
        "index": "All symptoms",
        "hooks": "Claude Code hooks",
        "ps": "PowerShell, Python, cmd",
        "footer": "By Kamijo Aoto. Covers what was verified on the author's machine.",
    },
}

CSS = """:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5a52;--line:#e2ded4;--card:#ffffff;--accent:#9a3412;--code:#f2efe8;--ok:#166534}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161513;--fg:#ecebe6;--muted:#a8a49a;--line:#34312b;--card:#1f1e1b;--accent:#f0a46a;--code:#26241f;--ok:#86efac}}
:root[data-theme="dark"]{--bg:#161513;--fg:#ecebe6;--muted:#a8a49a;--line:#34312b;--card:#1f1e1b;--accent:#f0a46a;--code:#26241f;--ok:#86efac}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 system-ui,-apple-system,"Segoe UI","Hiragino Sans","Yu Gothic UI",sans-serif}
main,header,footer{max-width:760px;margin:0 auto;padding:0 16px}
header{padding-top:20px;display:flex;justify-content:space-between;gap:12px;font-size:14px}
a{color:var(--accent)}
h1{font-size:1.6rem;line-height:1.35;margin:.6em 0 .4em}
h2{font-size:1.1rem;margin:2em 0 .5em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
.id{font:600 13px Consolas,"Cascadia Mono",Menlo,monospace;color:var(--muted)}
.lead{color:var(--muted)}
pre{position:relative;background:var(--code);border:1px solid var(--line);border-radius:8px;padding:40px 14px 14px;overflow-x:auto;font:13.5px/1.55 Consolas,"Cascadia Mono",Menlo,monospace;white-space:pre}
pre code{font-family:inherit}
pre button{position:absolute;top:8px;right:8px;font:12px system-ui;padding:4px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);cursor:pointer}
.note{font-size:14px;color:var(--muted)}
.result{background:var(--card);border-left:3px solid var(--ok);padding:10px 14px;border-radius:4px}
ul.tags{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px}
ul.tags li{border:1px solid var(--line);border-radius:999px;padding:2px 12px;font-size:14px;color:var(--muted)}
ol.list{padding:0;list-style:none}
ol.list li{border-bottom:1px solid var(--line);padding:12px 0}
ol.list a{text-decoration:none;font-weight:600}
.kit{margin-top:2.5em;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
footer{margin:40px auto;color:var(--muted);font-size:13px}
"""

JS = """document.querySelectorAll('pre').forEach(function(p){var b=document.createElement('button');b.type='button';b.textContent=COPY;b.addEventListener('click',function(){var t=p.querySelector('code').innerText;function done(){b.textContent=COPIED;setTimeout(function(){b.textContent=COPY},1500)}if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,function(){sel(p)})}else{sel(p)}});p.appendChild(b)});
function sel(p){var r=document.createRange();r.selectNodeContents(p.querySelector('code'));var s=getSelection();s.removeAllRanges();s.addRange(r)}"""

e = html.escape


def head(lang, title, desc, path, alt_path):
    other = "en" if lang == "ja" else "ja"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<link rel="alternate" hreflang="{lang}" href="{BASE}{path}">
<link rel="alternate" hreflang="{other}" href="{BASE}{alt_path}">
<link rel="stylesheet" href="../style.css">
</head>
<body>
"""


def page(tr, lang):
    t = T[lang]
    d = tr[lang]
    other = "en" if lang == "ja" else "ja"
    path = f"{lang}/{tr['id']}.html"
    desc = d["symptom"][:150]
    out = [head(lang, f"{d['title']} | {t['site']}", desc, path, f"{other}/{tr['id']}.html")]
    out.append(f'<header><a href="index.html">{e(t["index"])}</a><a href="../{other}/{tr["id"]}.html" hreflang="{other}">{e(t["other"])}</a></header>\n<main>\n')
    out.append(f'<p class="id">{tr["id"].upper()}</p>\n<h1>{e(d["title"])}</h1>\n')
    out.append(f'<h2>{e(t["symptom"])}</h2>\n<p>{e(d["symptom"])}</p>\n')
    note = t["check_note"]
    if tr.get("claude"):
        note += " " + t["check_claude"]
    if tr.get("slow"):
        note += " " + t["check_slow"]
    out.append(f'<h2>{e(t["check"])}</h2>\n<p class="note">{e(note)}</p>\n<pre><code>{e(tr["check"])}</code></pre>\n')
    out.append(f'<h2>{e(t["why"])}</h2>\n<p>{e(d["why"])}</p>\n')
    out.append(f'<h2>{e(t["fix"])}</h2>\n<p>{e(d["fix"])}</p>\n<pre><code>{e(d["fixcode"])}</code></pre>\n')
    out.append(f'<h2>{e(t["result"])}</h2>\n<p class="result">{e(d["result"])}</p>\n<p class="note">{e(AUTHOR_ENV[lang])}</p>\n')
    out.append(f'<h2>{e(t["search"])}</h2>\n<ul class="tags">' + "".join(f"<li>{e(s)}</li>" for s in d["search"]) + "</ul>\n")
    links = LINKS[lang]
    free = links["free_h"] if tr["id"].startswith("h") else links["free_t"]
    rel = [free] + ([links["repo"]] if links["repo"] and links["repo"] != free else [])
    out.append(f'<h2>{e(t["related"])}</h2>\n<ul>' + "".join(f'<li><a href="{u}">{e(n)}</a></li>' for n, u in rel) + "</ul>\n")
    kn, ku = links["kit"]
    out.append(f'<div class="kit"><p>{e(t["kit"])}</p><p><a href="{ku}">{e(kn)}</a></p></div>\n')
    out.append(f'<h2>{e(t["more"])}</h2>\n<ul>' + "".join(
        f'<li><a href="{o["id"]}.html">{e(o[lang]["title"])}</a></li>' for o in TRAPS if o["id"] != tr["id"]) + "</ul>\n")
    out.append(foot(lang))
    return "".join(out)


def foot(lang):
    t = T[lang]
    js = JS.replace("COPIED", repr(t["copied"])).replace("COPY", repr(t["copy"]))
    return f'</main>\n<footer>{e(t["footer"])}</footer>\n<script>{js}</script>\n</body>\n</html>\n'


def index(lang):
    t = T[lang]
    other = "en" if lang == "ja" else "ja"
    out = [head(lang, t["site"], t["lead"][:150], f"{lang}/index.html", f"{other}/index.html")]
    out.append(f'<header><span></span><a href="../{other}/index.html" hreflang="{other}">{e(t["other"])}</a></header>\n<main>\n')
    out.append(f'<h1>{e(t["site"])}</h1>\n<p class="lead">{e(t["lead"])}</p>\n')
    for head_key, prefix in (("hooks", "h"), ("ps", "t")):
        out.append(f'<h2>{e(t[head_key])}</h2>\n<ol class="list">')
        for tr in TRAPS:
            if tr["id"].startswith(prefix):
                out.append(f'<li><span class="id">{tr["id"].upper()}</span><br><a href="{tr["id"]}.html">{e(tr[lang]["title"])}</a></li>')
        out.append("</ol>\n")
    kn, ku = LINKS[lang]["kit"]
    out.append(f'<div class="kit"><p>{e(t["kit"])}</p><p><a href="{ku}">{e(kn)}</a></p></div>\n')
    out.append(foot(lang))
    return "".join(out)


def root_index():
    # language choice; English first for search, Japanese for the author's readers
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Windows Claude Code Traps</title>
<meta name="description" content="{e(T['en']['lead'][:150])}">
<link rel="canonical" href="{BASE}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<h1>{e(T['en']['site'])}</h1>
<p class="lead">{e(T['en']['lead'])}</p>
<p><a href="en/index.html">English</a> · <a href="ja/index.html" hreflang="ja">日本語</a></p>
</main>
</body>
</html>
"""


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    if CHECKS.exists():
        shutil.rmtree(CHECKS)
    for lang in ("ja", "en"):
        (DOCS / lang).mkdir(parents=True)
    CHECKS.mkdir()
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "index.html").write_text(root_index(), encoding="utf-8")
    urls = [BASE]
    for lang in ("ja", "en"):
        (DOCS / lang / "index.html").write_text(index(lang), encoding="utf-8")
        urls.append(f"{BASE}{lang}/index.html")
        for tr in TRAPS:
            (DOCS / lang / f"{tr['id']}.html").write_text(page(tr, lang), encoding="utf-8")
            urls.append(f"{BASE}{lang}/{tr['id']}.html")
    for tr in TRAPS:
        src = tr["check"]
        bad = [c for c in src if ord(c) > 127]
        if bad:
            raise SystemExit(f"{tr['id']}: check snippet must be ASCII-only, found {bad[:3]}")
        # CRLF so the file is also fine for anyone opening it in Notepad
        (CHECKS / f"{tr['id']}.ps1").write_bytes(src.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii") + b"\r\n")
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print(f"pages: {len(urls)}  checks: {len(TRAPS)}")


if __name__ == "__main__":
    main()
