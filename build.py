"""Build the static site into docs/ (GitHub Pages serves this folder) and the check scripts into checks/.
    python build.py
Everything comes from traps.py. Do not edit docs/ by hand.
"""
import datetime
import html
import json
import os
import pathlib
import re
import shutil

from traps import AUTHOR_ENV, BOOK_BY_TRAP, TRAPS

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
CHECKS = ROOT / "checks"
GALLERY = ROOT / "gallery"
# Assumed GitHub Pages address; change here if the repository lives elsewhere.
BASE = "https://cart231-ffly-b.github.io/cc-win-symptoms/"
DOCTOR_COMMAND = f"irm {BASE}doctor.ps1 | iex"
DOCTOR_VERSION = "1.0.0"
DOCTOR_GUID = "ee622f86-f1db-44e3-836c-aa9fa81cda6d"
DOCTOR_DESCRIPTION = "Checks which of 40 silent Windows failure modes for Claude Code and Codex CLI reproduce on this PC."
INDEXNOW_KEY = "5e01d4778f176e4b4d7c7fbda4d1fbcd"
TRAPS_REPO = "https://github.com/cart231-ffly-b/claude-code-windows-traps"
ZENN_AUTHOR = "https://zenn.dev/kamijo_aoto"
BOOK_URL = f"{ZENN_AUTHOR}/books/windows-claude-code-traps"
BOOK_OFFER = "Zenn・全章 1,200円／0〜4章は無料"
BOOK = ("0〜4章を無料で読む（Zenn、全章 1,200円）", BOOK_URL)
SLIDE_KATA = "https://cart231-ffly-b.github.io/slide-kata/"
BOOK_CHAPTERS = {
    2: ("02-encoding", "文字コードの対策"),
    3: ("03-exitcode-args", "終了コードと引数の対策"),
    4: ("04-files-tools", "ファイルと道具の対策"),
    5: ("05-guard", "安全装置の設計と実装"),
    6: ("06-runner", "夜の無人実行の仕組み"),
    8: ("08-safeinvoke", "PowerShell 5.1 から安全に呼ぶ関数"),
    9: ("09-claude-md", "CLAUDE.md の型"),
    12: ("12-november-claude-code", "Claude Code の追補"),
}
ZENN_ARTICLES = {
    "h04": ("日本語フォルダと拒否フックの検証記事（Zenn）", f"{ZENN_AUTHOR}/articles/claude-code-hook-japanese-path"),
    "h05": ("Windows のパスとフックの検証記事（Zenn）", f"{ZENN_AUTHOR}/articles/claude-code-hook-windows-path-127"),
}
GUIDES = {
    "hooks-guide.html": (
        "Claude Code のフックが効かない・素通りする原因と対策まとめ",
        "PreToolUse の拒否が素通りする、settings.json のフックが読まれない、パス判定がずれるときの確認手順。",
    ),
    "encoding-guide.html": (
        "Windows の日本語文字化けまとめ｜PowerShell・Python・Claude Code・Codex CLI",
        "パイプで日本語が ? になる、cp932 で UnicodeEncodeError が出るなど、見た目から原因と直し方を探せます。",
    ),
}

HOOK_GROUPS = (
    ("起動しない", ("h03", "h05", "h17", "h21")),
    ("拒否が通らない", ("h01", "h02", "h04")),
    ("パス判定がずれる", ("h19", "h23")),
)
ENCODING_GROUPS = (
    ("? になる", ("t04", "c01")),
    ("「譌･譛ｬ」「繝｡繝｢」のように化ける", ("t05", "c02")),
    ("UnicodeEncodeError で落ちる", ("t06", "t07")),
    ("構文エラーになるか、化けた文字を出す", ("t08",)),
    ("日本語のフォルダで拒否フックが素通りする", ("h04",)),
)
HOOK_IDS = {trap_id for _, ids in HOOK_GROUPS for trap_id in ids}
CATEGORIES = ("hooks", "tools", "ps", "codex")
SORTED_TRAPS = sorted(TRAPS, key=lambda tr: tr["id"])
TRAPS_BY_ID = {tr["id"]: tr for tr in TRAPS}

JA_REPO = ("PowerShell・Python・cmd の再現スクリプト cc-win-traps（無料、MIT）", TRAPS_REPO)
# The note articles go public on these dates. Before that, a link to them is a dead
# link, so the page points to something that already exists. Rebuild after each date.
PRIVACY = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Privacy policy for kaboomie-stats</title><link rel="stylesheet" href="style.css"></head><body>
<h1>Privacy policy for kaboomie-stats</h1>
<p>kaboomie-stats is a private tool used only by its operator. It reads statistics of the operator's own YouTube channel through the YouTube Data API and the YouTube Analytics API, and uploads the operator's own videos to that channel. It is not offered to anyone else.</p>
<ul>
<li>The daily statistics use read-only access. A separate permission, used only when the operator runs it, uploads the operator's own videos as private, schedules their publication, and sets their playlists, thumbnails and descriptions. It is not used to delete videos.</li>
<li>It reads channel and video statistics such as views, watch time and subscribers gained. It does not collect data about other people.</li>
<li>The numbers are stored on the operator's own PC and in the operator's personal cloud notes. They are not sold or given to anyone.</li>
<li>Access can be removed at any time from <a href="https://myaccount.google.com/permissions">Google Account permissions</a>.</li>
</ul>
<p>Questions: <a href="https://github.com/cart231-ffly-b/cc-win-symptoms/issues">GitHub issues</a>. Last updated: 2026-11-01.</p>
<hr>
<h2>日本語</h2>
<p>kaboomie-stats は運営者だけが使う道具です。運営者自身の YouTube チャンネルの数字を公式の API で読み取り、運営者自身の動画をそのチャンネルへ上げます。ほかの人には提供していません。</p>
<ul>
<li>毎日の数字の読み取りは読み取りの権限だけを使います。別の権限を、運営者が実行したときだけ使い、運営者自身の動画を非公開で上げ、公開日時の予約、再生リスト、サムネイル、説明欄の設定をします。動画の削除には使いません。</li>
<li>読むのはチャンネルと動画の数字（再生、視聴時間、増えた登録など）です。他人のデータは集めません。</li>
<li>数字は運営者の PC と個人のクラウドのノートに保存し、販売や第三者への提供はしません。</li>
<li>権限は <a href="https://myaccount.google.com/permissions">Google アカウントの権限のページ</a> からいつでも取り消せます。</li>
</ul>
</body></html>
"""
NOT_YET = "9999-12-31"  # note は 2026-11-01 時点で下書きのまま（URL は 404）。公開したら、その日付に変える
JA_NOTE = {
    "free_t": (NOT_YET, ("エラーなしで壊れる14か所（無料の記事）", "https://note.com/sodateru_ai/n/na7d9ee2a36fa"), JA_REPO),
    "free_h": (NOT_YET, ("安全フックは、遅れると黙って素通りする（無料の記事）", "https://note.com/sodateru_ai/n/n17e499f58486"), JA_REPO),
    "kit": (NOT_YET, ("cc-win-kit（note、2,980円）", "https://note.com/sodateru_ai/n/ndad0eb6feaa6"), BOOK),
}
# BUILD_DATE=2026-11-05 python build.py  shows what the site looks like on that day
TODAY = os.environ.get("BUILD_DATE") or datetime.date.today().isoformat()

LINKS = {
    "ja": dict({k: (live if TODAY >= day else before) for k, (day, live, before) in JA_NOTE.items()}, repo=JA_REPO),
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
        "index_title": "Windows で Claude Code が黙って壊れるとき — フック・PowerShell・Codex CLI の40症状と直し方",
        "lead": "エラーは出ないのに、結果だけが違う。Windows で起きる Claude Code のフックの素通りや、PowerShell・Codex CLI の文字化けなどの症状に、確かめ方・原因・直し方を添えました。どれも作者の PC で実際に起きたものです。",
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
        "book_intro": "安全装置、無人実行、CLAUDE.md の型の実装と設計は、Zenn の本にまとめています（全章 1,200円。0〜4章は無料）。",
        "copy": "コピー",
        "copied": "コピーしました",
        "other": "English",
        "doctor": "この PC でまとめて確かめる",
        "doctor_intro": "Windows PowerShell 5.1 に貼ると、この PC で再現する症状と、各症状のページを一覧で表示します。",
        "doctor_local": "データはアップロードしません。管理者権限は不要です。書き込み先は専用の一時フォルダだけで、実行後に削除します。",
        "doctor_skips": "通信が必要な Claude のチェックは省きます。時間のかかるローカルチェックを含めるには、先に $env:CCDOCTOR_ALL='1' を実行します。",
        "scoreboard": "Windows の症状を確認した週次結果",
        "index": "一覧へ",
        "hooks": "Claude Code のフック",
        "tools": "Claude Code のツール・CLAUDE.md",
        "ps": "PowerShell・Python・cmd",
        "codex": "Codex CLI（OpenAI）",
        "footer": "内容は作者の PC で確かめた範囲です。文章の下書きと確かめる実行は、AI（Claude Code）の手を借りています。",
    },
    "en": {
        "site": "When Claude Code breaks silently on Windows",
        "index_title": "When Claude Code breaks silently on Windows — 40 hook, PowerShell and Codex CLI symptoms and fixes",
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
        "doctor": "Check this PC",
        "doctor_intro": "Paste into Windows PowerShell 5.1 to see which symptoms reproduce on this PC and get a link to each symptom's page.",
        "doctor_local": "It uploads no data and needs no administrator rights. It writes only to its own temporary folder and removes that folder when it finishes.",
        "doctor_skips": "Checks that need Claude require a network connection and are skipped. To include the slow local check, first run $env:CCDOCTOR_ALL='1'.",
        "scoreboard": "Weekly Windows survival scoreboard",
        "index": "All symptoms",
        "hooks": "Claude Code hooks",
        "tools": "Claude Code tools and CLAUDE.md",
        "ps": "PowerShell, Python, cmd",
        "codex": "Codex CLI (OpenAI)",
        "footer": "Covers what was verified on the author's machine. Written with AI assistance: Claude Code drafted the text and ran the checks.",
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
.next-steps{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:1em 0}
.next-steps p{margin:.4em 0}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid var(--line)}
footer{margin:40px auto;color:var(--muted);font-size:13px}
"""

JS = """document.querySelectorAll('pre').forEach(function(p){var b=document.createElement('button');b.type='button';b.textContent=COPY;b.addEventListener('click',function(){var t=p.querySelector('code').innerText;function done(){b.textContent=COPIED;setTimeout(function(){b.textContent=COPY},1500)}if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,function(){sel(p)})}else{sel(p)}});p.appendChild(b)});
function sel(p){var r=document.createRange();r.selectNodeContents(p.querySelector('code'));var s=getSelection();s.removeAllRanges();s.addRange(r)}"""

e = html.escape
SENTENCE_END = re.compile(r'。|(?<!\.)[.!?]["”’]?(?=\s+[A-Z]|\s*$)')
URL = re.compile(r"""https?://[^\s<>"'、。！？（）「」『』]+""")
INDEX_ALTERNATES = {"ja": "ja/index.html", "en": "en/index.html", "x-default": ""}


def sentence_parts(text):
    start = 0
    for end in SENTENCE_END.finditer(text):
        yield text[start:end.end()].strip()
        start = end.end()
    if text[start:].strip():
        yield text[start:].strip()


def short_description(text, limit):
    if len(text) <= limit:
        return text
    sentences = [end.end() for end in SENTENCE_END.finditer(text) if end.end() <= limit]
    if sentences:
        return text[:sentences[-1]]
    spaces = list(re.finditer(r"\s+", text[:limit + 1]))
    return text[:spaces[-1].start()] if spaces else ""


def symptom_description(tr, lang):
    d = tr[lang]
    if lang == "ja":
        limit = 110
        tail = "確認コードと直し方を掲載。" if tr.get("claude") else "30秒で確かめるコードと直し方を掲載。"
    else:
        limit = 150
        tail = " Includes a check and a fix." if tr.get("claude") else " Includes a 30-second check and a fix."
    symptom = next(sentence_parts(d["symptom"]))
    # These symptoms start with setup or a shared outcome. The title identifies the failure.
    if tr["id"] in {"h01", "h04", "h05", "t03", "t12"} or len(symptom + tail) > limit:
        symptom = d["title"]
        if len(symptom + tail) >= limit and symptom.endswith(")"):
            symptom = symptom.rsplit(" (", 1)[0]
        if not symptom.endswith(("。", ".", "!", "?")):
            symptom += "。" if lang == "ja" else "."
    return symptom + tail


def anchor(label, url):
    return f'<a href="{e(url)}">{e(label)}</a>'


def chapter_link(number):
    slug, subject = BOOK_CHAPTERS[number]
    if number <= 4:
        return (f"本の{number}章で{subject}を読む（Zenn・無料）", f"{BOOK_URL}/viewer/{slug}")
    return (f"本の{number}章で{subject}を読む（{BOOK_OFFER}）", BOOK_URL)


def linkify(text):
    parts = []
    start = 0
    chapter = re.search(r"本の([0-9]+)章", text)
    for match in URL.finditer(text):
        url = match.group().rstrip(".,;:!?)]}")
        parts.append(e(text[start:match.start()]))
        if url == BOOK_URL and chapter:
            label, target = chapter_link(int(chapter[1]))
            parts.append(anchor(label.removeprefix(f"本の{chapter[1]}章で"), target))
        else:
            parts.append(anchor(url, url))
        start = match.start() + len(url)
    parts.append(e(text[start:]))
    return "".join(parts)


def card(title, desc, url, og_type):
    # share card for X / Slack / Discord; the image comes from make_og.py
    return (f'<meta property="og:type" content="{og_type}">\n<meta property="og:title" content="{e(title)}">\n'
            f'<meta property="og:description" content="{e(desc)}">\n<meta property="og:url" content="{url}">\n'
            f'<meta property="og:image" content="{BASE}og.png">\n<meta name="twitter:card" content="summary_large_image">\n')


def collection_data(lang, title, path):
    return [
        {"@type": "WebSite", "@id": BASE + "#website", "url": BASE, "name": T["en"]["site"]},
        {"@type": "CollectionPage", "name": title, "url": BASE + path, "inLanguage": lang,
         "isPartOf": {"@id": BASE + "#website"}},
    ]


def article_data(lang, title, desc, path):
    return [
        {"@type": "TechArticle", "headline": title, "description": desc, "url": BASE + path,
         "inLanguage": lang, "image": BASE + "og.png",
         "author": {"@type": "Person", "name": "Kamijo Aoto", "url": ZENN_AUTHOR}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": T[lang]["index"], "item": f"{BASE}{lang}/index.html"},
            {"@type": "ListItem", "position": 2, "name": title, "item": BASE + path},
        ]},
    ]


def head(lang, title, desc, path, data, *, alternates=None, og_type="website"):
    alternate_links = "".join(f'<link rel="alternate" hreflang="{locale}" href="{BASE}{alternate_path}">\n'
                              for locale, alternate_path in (alternates or {}).items())
    structured = json.dumps({"@context": "https://schema.org", "@graph": data}, ensure_ascii=False)
    structured = structured.replace("<", r"\u003c")
    stylesheet = "../style.css" if "/" in path else "style.css"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
{alternate_links}{card(title, desc, BASE + path, og_type)}<script type="application/ld+json">{structured}</script>
<link rel="stylesheet" href="{stylesheet}">
</head>
<body>
"""


def category(trap_id):
    if trap_id in HOOK_IDS:
        return "hooks"
    return {"h": "tools", "t": "ps", "c": "codex"}[trap_id[0]]


def trap_link(tr, lang):
    return anchor(tr[lang]["title"], f"{tr['id']}.html")


def related_traps(trap_id):
    cross_category = {"t04": ("t05", "t06", "c01"), "c01": ("c02", "t04", "t05"),
                      "c02": ("c01", "t05", "t08")}
    ids = list(cross_category.get(trap_id, ()))
    peers = [tr["id"] for tr in SORTED_TRAPS if category(tr["id"]) == category(trap_id)
             and tr["id"] != trap_id and tr["id"] not in ids]
    peers.sort(key=lambda peer: abs(int(peer[1:]) - int(trap_id[1:])))
    return [TRAPS_BY_ID[peer] for peer in (ids + peers)[:4]]


def kit_box(lang):
    t = T[lang]
    intro = t["book_intro"] if lang == "ja" and TODAY < JA_NOTE["kit"][0] else t["kit"]
    return f'<div class="kit"><p>{e(intro)}</p><p>{anchor(*LINKS[lang]["kit"])}</p></div>\n'


def doctor_link(lang):
    label = "doctor.ps1 の診断コマンドを表示" if lang == "ja" else "See the doctor.ps1 command"
    return anchor(label, "index.html#doctor")


def fix_steps(lang):
    if lang == "ja":
        return ('<div class="next-steps">\n'
                f'<p>この PC でほかの症状も起きるか調べる。{doctor_link(lang)}</p>\n'
                f'<p>再発を防ぐ設計と実装を読む。{anchor(*BOOK)}</p>\n</div>\n')
    return ('<div class="next-steps">\n'
            f'<p>Check which other symptoms occur on this PC. {doctor_link(lang)}</p>\n'
            f'<p>Get the tools to prevent these traps. {anchor(*LINKS[lang]["kit"])}</p>\n</div>\n')


def page(tr, lang):
    t = T[lang]
    d = tr[lang]
    other = "en" if lang == "ja" else "ja"
    path = f"{lang}/{tr['id']}.html"
    desc = symptom_description(tr, lang)
    alternates = {locale: f"{locale}/{tr['id']}.html" for locale in ("ja", "en")}
    alternates["x-default"] = alternates["en"]
    out = [head(lang, f"{d['title']} | {t['site']}", desc, path, article_data(lang, d["title"], desc, path),
                alternates=alternates, og_type="article")]
    out.append(f'<header><a href="index.html">{e(t["index"])}</a><a href="../{other}/{tr["id"]}.html" hreflang="{other}">{e(t["other"])}</a></header>\n<main>\n')
    out.append(f'<p class="id">{tr["id"].upper()}</p>\n<h1>{e(d["title"])}</h1>\n')
    out.append(f'<p class="lead">{e(" · ".join(d["search"][:2]))}</p>\n')
    out.append(f'<h2>{e(t["symptom"])}</h2>\n<p>{e(d["symptom"])}</p>\n')
    note = t["check_note"]
    if tr.get("claude"):
        note += " " + t["check_claude"]
    if tr.get("slow"):
        note += " " + t["check_slow"]
    out.append(f'<h2>{e(t["check"])}</h2>\n<p class="note">{e(note)}</p>\n<pre><code>{e(tr["check"])}</code></pre>\n')
    out.append(f'<h2>{e(t["why"])}</h2>\n<p>{e(d["why"])}</p>\n')
    fix_title = f'{t["fix"]}（onFailure: block）' if tr["id"] == "h01" and lang == "ja" else t["fix"]
    out.append(f'<h2>{e(fix_title)}</h2>\n<p>{linkify(d["fix"])}</p>\n<pre><code>{e(d["fixcode"])}</code></pre>\n')
    out.append(fix_steps(lang))
    if lang == "ja" and tr["id"] in BOOK_BY_TRAP:
        out.append(f'<p>{anchor(*chapter_link(BOOK_BY_TRAP[tr["id"]]))}</p>\n')
    out.append(f'<h2>{e(t["result"])}</h2>\n<p class="result">{e(d["result"])}</p>\n<p class="note">{e(AUTHOR_ENV[lang])}</p>\n')
    out.append(f'<h2>{e(t["search"])}</h2>\n<ul class="tags">' + "".join(f"<li>{e(s)}</li>" for s in d["search"]) + "</ul>\n")
    links = LINKS[lang]
    free = links["free_h"] if tr["id"].startswith("h") else links["free_t"]
    rel = [free] + ([links["repo"]] if links["repo"] and links["repo"] != free else [])
    if lang == "ja" and tr["id"] in ZENN_ARTICLES:
        rel.append(ZENN_ARTICLES[tr["id"]])
    out.append(f'<h2>{e(t["related"])}</h2>\n<ul><li>{doctor_link(lang)}</li>'
               + "".join(f'<li>{anchor(*link)}</li>' for link in rel) + "</ul>\n")
    out.append(kit_box(lang))
    out.append(f'<h2>{e(t["more"])}</h2>\n<ul>' + "".join(
        f'<li>{trap_link(o, lang)}</li>' for o in related_traps(tr["id"])) + "</ul>\n"
        + f'<p>{anchor(t["index"], "index.html")}</p>\n')
    out.append(foot(lang))
    return "".join(out)


def foot(lang, prefix="../"):
    t = T[lang]
    js = JS.replace("COPIED", repr(t["copied"])).replace("COPY", repr(t["copy"]))
    if lang == "ja":
        author = "作者 " + anchor("上条碧斗（Kamijo Aoto）", ZENN_AUTHOR)
        links = [("Zenn の本（1,200円・0〜4章無料）", BOOK_URL), ("GitHub（cc-win-traps）", TRAPS_REPO),
                 ("週次結果", f"{prefix}scoreboard/ja.html"), ("作者の別サイト「スライドの型の棚」", SLIDE_KATA)]
    else:
        author = "By " + anchor("Kamijo Aoto", ZENN_AUTHOR)
        links = [("GitHub (cc-win-traps)", TRAPS_REPO), LINKS["en"]["kit"],
                 ("Weekly results", f"{prefix}scoreboard/index.html")]
    footer_links = " · ".join(anchor(*link) for link in links)
    return (f'</main>\n<footer><p>{author}</p>\n<p>{footer_links}</p>\n<p>{e(t["footer"])}</p></footer>\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def index(lang):
    t = T[lang]
    other = "en" if lang == "ja" else "ja"
    scoreboard_page = "ja.html" if lang == "ja" else "index.html"
    path = f"{lang}/index.html"
    title = t["index_title"]
    out = [head(lang, title, short_description(t["lead"], 150), path, collection_data(lang, title, path),
                alternates=INDEX_ALTERNATES)]
    out.append(f'<header><span></span><a href="../{other}/index.html" hreflang="{other}">{e(t["other"])}</a></header>\n<main>\n')
    out.append(f'<h1>{e(t["site"])}</h1>\n<p class="lead">{e(t["lead"])}</p>\n')
    out.append(f'<h2 id="doctor">{e(t["doctor"])}</h2>\n<p>{e(t["doctor_intro"])}</p>\n'
               f'<pre><code>{e(DOCTOR_COMMAND)}</code></pre>\n<p>{e(t["doctor_local"])}</p>\n'
               f'<p>{e(t["doctor_skips"])}</p>\n'
               f'<p><a href="../scoreboard/{scoreboard_page}">{e(t["scoreboard"])}</a></p>\n')
    if lang == "ja":
        out.append(f'<p>{anchor(*BOOK)}</p>\n')
        out.append('<ul>' + "".join(f'<li>{anchor(title, filename)}</li>' for filename, (title, _) in GUIDES.items())
                   + '</ul>\n')
    for head_key in CATEGORIES:
        out.append(f'<h2>{e(t[head_key])}</h2>\n<ol class="list">')
        for tr in SORTED_TRAPS:
            if category(tr["id"]) == head_key:
                out.append(f'<li><span class="id">{tr["id"].upper()}</span><br>{trap_link(tr, lang)}</li>')
        out.append("</ol>\n")
    out.append(kit_box(lang))
    out.append(foot(lang))
    return "".join(out)


def root_index():
    # language choice; English first for search, Japanese for the author's readers
    t = T["en"]
    title = t["site"]
    return (head("en", title, short_description(t["lead"], 150), "", collection_data("en", title, ""),
                 alternates=INDEX_ALTERNATES) + f"""<main>
<h1>{e(title)}</h1>
<p class="lead">{e(t['lead'])}</p>
<p><a href="en/index.html">English</a> · <a href="ja/index.html" hreflang="ja">日本語</a></p>
""" + foot("en", prefix=""))


def guide_table(headings, rows):
    header = "".join(f'<th scope="col">{e(heading)}</th>' for heading in headings)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n" for row in rows)
    return f'<div class="table-wrap"><table>\n<thead><tr>{header}</tr></thead>\n<tbody>\n{body}</tbody>\n</table></div>\n'


def hooks_guide():
    out = []
    for heading, ids in HOOK_GROUPS:
        out.append(f"<h2>{e(heading)}</h2>\n")
        rows = []
        for trap_id in ids:
            tr = TRAPS_BY_ID[trap_id]
            rows.append((trap_link(tr, "ja"), e(tr["ja"]["symptom"])))
        out.append(guide_table(("症状ページ", "起きること"), rows))
    out.append("<h2>設定を確かめる手順</h2>\n<ol>\n")
    for trap_id, count in (("h03", 2), ("h17", 2), ("h05", 1), ("h02", 1), ("h21", 2), ("h01", 2)):
        tr = TRAPS_BY_ID[trap_id]
        steps = "".join(list(sentence_parts(tr["ja"]["fix"]))[:count])
        out.append(f'<li>{e(steps)}（{anchor(trap_id.upper(), f"{trap_id}.html")}）</li>\n')
    out.append(f'</ol>\n<p>{anchor(*chapter_link(5))} · {doctor_link("ja")}</p>\n')
    return "".join(out)


def encoding_guide():
    rows = []
    for appearance, ids in ENCODING_GROUPS:
        for trap_id in ids:
            tr = TRAPS_BY_ID[trap_id]
            why = list(sentence_parts(tr["ja"]["why"]))
            cause = "".join(why[:2] if trap_id in {"t04", "t05", "t06", "t08", "h04", "c01"} else why[:1])
            rows.append((e(appearance), trap_link(tr, "ja"), f'<p>{e(cause)}</p><p>{linkify(tr["ja"]["fix"])}</p>'))
    roles = []
    for setting, trap_id, field in (
        ("$OutputEncoding", "t04", "why"),
        ("[Console]::OutputEncoding", "t05", "why"),
        ("PYTHONIOENCODING", "t06", "fix"),
        ("BOM", "t08", "fix"),
    ):
        definition = next(sentence_parts(TRAPS_BY_ID[trap_id]["ja"][field]))
        roles.append((f"<code>{e(setting)}</code>", e(definition)))
    return (f'<p>手元の PC でどの症状が再現するかをまとめて確かめる。{doctor_link("ja")}</p>\n'
            '<h2>文字化けの見た目から探す</h2>\n'
            + guide_table(("見た目", "症状ページ", "原因と直し方"), rows)
            + '<h2>文字コードの設定とファイル形式</h2>\n'
            + guide_table(("設定・形式", "役割と使い方"), roles)
            + f'<p>{anchor(*BOOK)} · {anchor(*JA_REPO)}</p>\n')


def guide(filename, content):
    title, desc = GUIDES[filename]
    path = f"ja/{filename}"
    return (head("ja", title, desc, path, collection_data("ja", title, path))
            + f'<header>{anchor(T["ja"]["index"], "index.html")}</header>\n<main>\n'
            + f'<h1>{e(title)}</h1>\n<p class="lead">{e(desc)}</p>\n'
            + content + foot("ja"))


def write_doctor():
    data = [{
        "id": tr["id"],
        "ja": tr["ja"]["title"],
        "en": tr["en"]["title"],
        "claude": tr.get("claude", False),
        "slow": tr.get("slow", False),
        "check": (CHECKS / f"{tr['id']}.ps1").read_bytes().decode("ascii"),
    } for tr in TRAPS]
    messages = {
        "ja": {
            "header": "ID  結果  症状  |  ページ",
            "statuses": {
                "REPRODUCED": "起きる",
                "NOT REPRODUCED": "起きない",
                "CANNOT CHECK": "調べられない",
                "TIMEOUT": "時間切れ",
            },
            "summary": "この PC では、調べた {0} 件のうち {1} 件が起きました。各行のページに直し方があります。",
            "skipped_claude": "Claude を呼ぶ {0} 件は、使用量を使うので調べていません。一覧: {1}",
            "skipped_slow": "t13 も調べるには、$env:CCDOCTOR_ALL='1' を実行してからもう一度お試しください。",
        },
        "en": {
            "header": "ID  Result  Symptom  |  Page",
            "statuses": {
                "REPRODUCED": "REPRODUCED",
                "NOT REPRODUCED": "NOT REPRODUCED",
                "CANNOT CHECK": "CANNOT CHECK",
                "TIMEOUT": "TIMEOUT",
            },
            "summary": "{1} of {0} checks reproduce on this PC. Each row's page has the fix.",
            "skipped_claude": "Skipped {0} that would call Claude and count toward your usage. Index: {1}",
            "skipped_slow": "To include t13, run $env:CCDOCTOR_ALL='1' before running the doctor again.",
        },
    }
    template = (ROOT / "doctor.template.ps1").read_text(encoding="ascii")
    rows = ",\n".join(json.dumps(tr) for tr in data)
    script = (template.replace("__BASE__", BASE)
              .replace("__MESSAGES__", json.dumps(messages, indent=4))
              .replace("__TRAPS__", f"[\n{rows}\n]"))
    (DOCS / "doctor.ps1").write_text(script, encoding="ascii")
    header = f"""<#PSScriptInfo

.VERSION {DOCTOR_VERSION}
.GUID {DOCTOR_GUID}
.AUTHOR Aoto Kamijo
.DESCRIPTION {DOCTOR_DESCRIPTION}
.TAGS Windows ClaudeCode Codex PowerShell Encoding Diagnostics
.LICENSEURI https://github.com/cart231-ffly-b/cc-win-symptoms/blob/main/LICENSE
.PROJECTURI {BASE}
.RELEASENOTES
Initial release.

#>

<#
.DESCRIPTION
{DOCTOR_DESCRIPTION}
#>

"""
    GALLERY.mkdir(exist_ok=True)
    (GALLERY / "CCDoctor.ps1").write_text(header + script, encoding="ascii")


def write_llms():
    t = T["en"]
    index_lines = [
        f"# {t['site']}", "", f"> {DOCTOR_DESCRIPTION}", "",
        f"`{DOCTOR_COMMAND}`",
    ]
    for heading in CATEGORIES:
        index_lines.extend(["", f"## {t[heading]}", ""])
        for tr in SORTED_TRAPS:
            if category(tr["id"]) == heading:
                index_lines.append(f"- [{tr['en']['title']}]({BASE}en/{tr['id']}.html)")
    index_lines.extend([
        "", "## Resources / Books & Tools", "",
        f"- [Japanese index]({BASE}ja/index.html)",
        f"- [Windows × Claude Code book (Zenn, in Japanese)]({BOOK_URL})",
        f"- [cc-win-traps (GitHub)]({TRAPS_REPO})",
        f"- [{LINKS['en']['kit'][0]}]({LINKS['en']['kit'][1]})",
        f"- [Weekly results]({BASE}scoreboard/index.html)",
        f"- [Weekly results in Japanese]({BASE}scoreboard/ja.html)",
    ])
    index_lines.extend(["", "## Optional", "", f"- [All symptoms in plain text]({BASE}llms-full.txt)"])
    (DOCS / "llms.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    entries = []
    for tr in TRAPS:
        d = tr["en"]
        entries.append(
            f"{tr['id']}\n{d['title']}\n\n"
            f"{t['symptom']}\n{d['symptom']}\n\n"
            f"{t['why']}\n{d['why']}\n\n"
            f"{t['check']}\n{tr['check']}\n\n"
            f"{t['fix']}\n{d['fix']}\n{d['fixcode']}"
        )
    (DOCS / "llms-full.txt").write_text("\n\n".join(entries) + "\n", encoding="utf-8")


def main():
    if DOCS.exists():
        for child in DOCS.iterdir():
            if child.name == "scoreboard":
                continue  # The weekly workflow maintains this directory and its history.
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    if CHECKS.exists():
        shutil.rmtree(CHECKS)
    for lang in ("ja", "en"):
        (DOCS / lang).mkdir(parents=True)
    CHECKS.mkdir()
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "privacy.html").write_text(PRIVACY, encoding="utf-8")
    # Google Search Console の所有者確認。消すと確認が外れる
    name = "google35a4e9116c54b951.html"
    (DOCS / name).write_text(f"google-site-verification: {name}", encoding="utf-8", newline="")
    # IndexNow（Bing など）の鍵。公開してよい値（仕組み上、誰でも読める）。ai-staff の jobs/michi.py が同じ値で知らせる。
    # 置き場はこのフォルダの下（Option 2）なので、知らせてよいのは /cc-win-symptoms/ の下の URL だけ
    (DOCS / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8", newline="")
    shutil.copyfile(ROOT / "assets" / "og.png", DOCS / "og.png")
    (DOCS / "index.html").write_text(root_index(), encoding="utf-8")
    urls = [BASE]
    for lang in ("ja", "en"):
        (DOCS / lang / "index.html").write_text(index(lang), encoding="utf-8")
        urls.append(f"{BASE}{lang}/index.html")
        for tr in TRAPS:
            (DOCS / lang / f"{tr['id']}.html").write_text(page(tr, lang), encoding="utf-8")
            urls.append(f"{BASE}{lang}/{tr['id']}.html")
    for filename, content in (("hooks-guide.html", hooks_guide()), ("encoding-guide.html", encoding_guide())):
        (DOCS / "ja" / filename).write_text(guide(filename, content), encoding="utf-8")
        urls.append(f"{BASE}ja/{filename}")
    for path in ("scoreboard/index.html", "scoreboard/ja.html"):
        if (DOCS / path).is_file():
            urls.append(BASE + path)
    for tr in TRAPS:
        src = tr["check"]
        bad = [c for c in src if ord(c) > 127]
        if bad:
            raise SystemExit(f"{tr['id']}: check snippet must be ASCII-only, found {bad[:3]}")
        # CRLF so the file is also fine for anyone opening it in Notepad
        (CHECKS / f"{tr['id']}.ps1").write_bytes(src.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii") + b"\r\n")
    write_doctor()
    write_llms()
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print(f"pages: {len(urls)}  checks: {len(TRAPS)}  links as of: {TODAY}")


if __name__ == "__main__":
    main()
