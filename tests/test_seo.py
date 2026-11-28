from html import unescape
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build


def test_urls_in_fix_are_links():
    assert build.linkify('See (https://example.com/?a=1&b=2). <tag>') == (
        'See (<a href="https://example.com/?a=1&amp;b=2">'
        'https://example.com/?a=1&amp;b=2</a>). &lt;tag&gt;'
    )


def test_book_links_across_generated_site(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    monkeypatch.setattr(build, "DOCS", docs)
    monkeypatch.setattr(build, "CHECKS", tmp_path / "checks")
    monkeypatch.setattr(build, "GALLERY", tmp_path / "gallery")
    build.main()

    original = {path.relative_to(docs): path.read_bytes() for path in docs.rglob("*") if path.is_file()}
    old_url = build.BOOK["url"]
    old_url_bytes = old_url.encode()
    for path, content in original.items():
        assert b"books/windows-claude-code-traps/viewer/" not in content, path
        urls = re.findall(rb'https?://[^\s<>"\')]+', content)
        assert all(url == old_url_bytes for url in urls
                   if url.startswith(old_url_bytes) or b"/books/windows-claude-code-traps" in url), path

    href = f'href="{build.e(old_url)}"'
    link = f'<a {href}>{build.e(build.BOOK["label"])}</a>'
    symptom_pages = {f"{tr['id']}.html" for tr in build.TRAPS}
    for name in symptom_pages | set(build.GUIDES) | {"index.html"}:
        page = (docs / "ja" / name).read_text(encoding="utf-8")
        graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page)[1])["@graph"]
        assert {"@type": "Book", "url": old_url} in [node.get("mentions") for node in graph], name
        if name in symptom_pages:
            assert page.count(href) == 1, name
            assert link in re.search(r'<div class="next-steps">(.*?)</div>', page, re.S)[1], name
        else:
            assert link in page.split("<footer>", 1)[1], name
    assert f"- [{build.BOOK['label_en']}]({old_url})" in (docs / "llms.txt").read_text(encoding="utf-8")

    new_url = "https://example.com/kindle-book"
    monkeypatch.setitem(build.BOOK, "url", new_url)
    build.main()
    switched = {path.relative_to(docs): path.read_bytes() for path in docs.rglob("*") if path.is_file()}
    assert switched == {path: content.replace(old_url_bytes, new_url.encode()) for path, content in original.items()}


def test_description_uses_sentence_or_word_boundaries():
    assert build.short_description("最初の文。続きの文です。", 9) == "最初の文。"
    assert build.short_description("First sentence. Next sentence.", 22) == "First sentence."
    assert build.short_description("PowerShell output encoding", 20) == "PowerShell output"
    assert build.short_description("An error in a .ps1 file", 20) == "An error in a .ps1"

    for lang, limit in (("ja", 110), ("en", 150)):
        for trap in build.TRAPS:
            rendered = build.page(trap, lang)
            desc = unescape(re.search(r'<meta name="description" content="([^"]+)">', rendered)[1])
            assert 0 < len(desc) <= limit, (lang, trap["id"], desc)
            if lang == "ja":
                assert desc.count("。") >= 2
            else:
                assert re.search(r'[.!?]["”’]? Includes a ', desc)


@pytest.mark.parametrize("lang", ["ja", "en"])
def test_json_ld_and_alternates(lang):
    article = build.page(build.TRAPS_BY_ID["t04"], lang)
    for rendered, types in (
        (article, ["TechArticle", "BreadcrumbList"]),
        (build.index(lang), ["WebSite", "CollectionPage"]),
        (build.root_index(), ["WebSite", "CollectionPage"]),
    ):
        structured = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', rendered)[1])
        assert structured["@context"] == "https://schema.org"
        assert [node["@type"] for node in structured["@graph"]] == types
        assert all(f'hreflang="{locale}"' in rendered for locale in ("ja", "en", "x-default"))
    assert 'property="og:type" content="article"' in article


@pytest.mark.parametrize("scoreboard_exists", [False, True])
def test_sitemap_includes_guides_and_existing_scoreboard(tmp_path, monkeypatch, scoreboard_exists):
    docs = tmp_path / "docs"
    monkeypatch.setattr(build, "DOCS", docs)
    monkeypatch.setattr(build, "CHECKS", tmp_path / "checks")
    monkeypatch.setattr(build, "GALLERY", tmp_path / "gallery")
    scoreboard_paths = ("scoreboard/index.html", "scoreboard/ja.html")
    if scoreboard_exists:
        (docs / "scoreboard").mkdir(parents=True)
        for path in scoreboard_paths:
            (docs / path).touch()

    build.main()
    sitemap = ElementTree.parse(docs / "sitemap.xml")
    paths = {node.text.removeprefix(build.BASE) for node in sitemap.findall(".//{*}loc")}
    assert {"ja/hooks-guide.html", "ja/encoding-guide.html"} <= paths
    for path in scoreboard_paths:
        assert (path in paths) == scoreboard_exists
