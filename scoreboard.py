"""Render the doctor results at CCDOCTOR_JSON into docs/scoreboard/."""

from datetime import UTC, datetime
from html import escape
import json
import os
from pathlib import Path
import platform
import subprocess

from build import DOCS, head
from traps import TRAPS


TRAPS_BY_ID = {trap["id"]: trap for trap in TRAPS}
PAGES = {"en": "index.html", "ja": "ja.html"}
TEXT = {
    "en": {
        "title": "Weekly Windows survival scoreboard",
        "note": "The GitHub Actions runner uses English-locale Windows (code page 437). "
                "Checks specific to a Japanese locale may show NOT REPRODUCED there. "
                "Each check’s page shows the author’s results on a Japanese PC.",
        "index": "All symptoms",
        "date": "Date (UTC)",
        "image": "Runner image",
        "local": "Local run on this PC",
        "windows": "Windows version",
        "locale": "Windows locale (OEM code page)",
        "checks": "Check results",
    },
    "ja": {
        "title": "Windows の症状を確認した週次結果",
        "note": "GitHub Actions のランナーは英語ロケールの Windows（コードページ 437）を使います。"
                "日本語ロケール固有の症状は、ランナーでは「起きない（NOT REPRODUCED）」になることがあります。"
                "作者の日本語環境の PC での結果は、各症状のページにあります。",
        "index": "症状一覧",
        "date": "実行日（UTC）",
        "image": "ランナーイメージ",
        "local": "この PC でのローカル実行",
        "windows": "Windows のバージョン",
        "locale": "Windows ロケール（OEM コードページ）",
        "checks": "確認結果",
    },
}
JA_STATUS = {
    "REPRODUCED": "起きる",
    "NOT REPRODUCED": "起きない",
    "CANNOT CHECK": "調べられない",
    "TIMEOUT": "時間切れ",
}


def windows_environment():
    command = "'{0},{1},{2}' -f $PSVersionTable.PSVersion, (Get-Culture).Name, (Get-Culture).TextInfo.OEMCodePage"
    output = subprocess.check_output(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        encoding="ascii",
    )
    powershell, locale, code_page = output.strip().split(",")
    return {
        "runner_image": " ".join(filter(None, (os.getenv("ImageOS"), os.getenv("ImageVersion")))),
        "windows_version": platform.version(),
        "powershell_version": powershell,
        "python_version": platform.python_version(),
        "locale": locale,
        "oem_code_page": int(code_page),
    }


def render_badge(reproduced, total):
    score = f"{reproduced}/{total} reproduce"
    label_width = 88
    score_width = 16 + 6 * len(score)
    width = label_width + score_width
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="windows traps | {score}">
  <title>windows traps | {score}</title>
  <clipPath id="badge"><rect width="{width}" height="20" rx="3"/></clipPath>
  <g clip-path="url(#badge)">
    <rect width="{width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{score_width}" height="20" fill="#166534"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana, sans-serif" font-size="11">
    <text x="{label_width / 2:g}" y="14">windows traps</text>
    <text x="{label_width + score_width / 2:g}" y="14">{score}</text>
  </g>
</svg>
"""


def render_html(lang, latest):
    t = TEXT[lang]
    other = "ja" if lang == "en" else "en"
    other_label = "日本語" if other == "ja" else "English"
    env = latest["environment"]
    metadata = [
        (t["date"], latest["date"]),
        (t["image"], env["runner_image"] or t["local"]),
        (t["windows"], env["windows_version"]),
        ("PowerShell", env["powershell_version"]),
        ("Python", env["python_version"]),
        (t["locale"], f'{env["locale"]} ({env["oem_code_page"]})'),
    ]
    lines = [
        head(lang, t["title"], t["note"], f"scoreboard/{PAGES[lang]}", f"scoreboard/{PAGES[other]}"),
        f'<header><a href="../{lang}/index.html">{t["index"]}</a>'
        f'<a href="{PAGES[other]}" hreflang="{other}">{other_label}</a></header>\n',
        f'<main>\n<h1>{t["title"]}</h1>\n',
        f'<p><img src="badge.svg" alt="windows traps | {latest["reproduced"]}/{latest["total"]} reproduce"></p>\n',
        '<dl>\n',
    ]
    for label, value in metadata:
        lines.append(f'<dt>{escape(label)}</dt><dd>{escape(value)}</dd>\n')
    lines.append(f'</dl>\n<p class="note">{t["note"]}</p>\n<h2>{t["checks"]}</h2>\n<ol class="list">\n')
    for row in latest["results"]:
        trap_id = row["id"]
        title = TRAPS_BY_ID[trap_id][lang]["title"]
        status = JA_STATUS[row["status"]] if lang == "ja" else row["status"]
        detail = f' <span class="note">({escape(row["detail"])})</span>' if row["detail"] else ""
        lines.append(
            f'<li><span class="id">{trap_id.upper()}</span> <strong>{escape(status)}</strong>{detail}<br>\n'
            f'<a href="../{lang}/{trap_id}.html">{escape(title)}</a></li>\n'
        )
    lines.append('</ol>\n</main>\n</body>\n</html>\n')
    return "".join(lines)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_scoreboard(results_path, output_dir, environment, date):
    results = json.loads(results_path.read_text(encoding="utf-8-sig"))
    summary = {
        "date": date,
        "reproduced": sum(row["status"] == "REPRODUCED" for row in results),
        "total": len(results),
    }
    latest = {**summary, "environment": environment, "results": results}
    pages = {filename: render_html(lang, latest) for lang, filename in PAGES.items()}
    history_path = output_dir / "history.json"
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    history.append(summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "latest.json", latest)
    (output_dir / "badge.svg").write_text(render_badge(summary["reproduced"], summary["total"]), encoding="utf-8")
    for filename, page in pages.items():
        (output_dir / filename).write_text(page, encoding="utf-8")
    write_json(history_path, history[-104:])


def main():
    results = os.environ.get("CCDOCTOR_JSON")
    if not results:
        raise SystemExit("Set CCDOCTOR_JSON to the doctor results file.")
    render_scoreboard(Path(results), DOCS / "scoreboard", windows_environment(), datetime.now(UTC).date().isoformat())


if __name__ == "__main__":
    main()
