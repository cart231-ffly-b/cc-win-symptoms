"""Static checks on docs/: page count, every relative link resolves, ja/en pairs, title and description.
    python check_links.py      (exit 0 = all good)
"""
import pathlib
import re
import sys

from traps import TRAPS

DOCS = pathlib.Path(__file__).resolve().parent / "docs"
problems = []
pages = sorted(DOCS.rglob("*.html"))
want = 1 + 2 * (1 + len(TRAPS))
if len(pages) != want:
    problems.append(f"expected {want} pages, found {len(pages)}")

for p in pages:
    text = p.read_text(encoding="utf-8")
    rel = p.relative_to(DOCS).as_posix()
    if not re.search(r"<title>[^<]{5,}</title>", text):
        problems.append(f"{rel}: no title")
    if 'name="description" content=""' in text or 'name="description"' not in text:
        problems.append(f"{rel}: no description")
    for href in re.findall(r'(?:href|src)="([^"]+)"', text):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (p.parent / href).resolve()
        if not target.exists():
            problems.append(f"{rel}: broken link {href}")
    if re.search(r"[가-힣]", text):
        problems.append(f"{rel}: Hangul found (generated text check)")

for tr in TRAPS:
    for lang in ("ja", "en"):
        if not (DOCS / lang / f"{tr['id']}.html").exists():
            problems.append(f"missing {lang}/{tr['id']}.html")

for line in problems:
    print("PROBLEM", line)
print(f"pages={len(pages)} problems={len(problems)}")
sys.exit(1 if problems else 0)
