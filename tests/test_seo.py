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
    for trap in build.TRAPS:
        fix = trap["ja"]["fix"]
        if build.BOOK_URL not in fix:
            continue
        rendered = build.page(trap, "ja")
        paragraph = re.search(r"<h2>直し方</h2>\s*<p>(.*?)</p>", rendered)[1]
        href, label = re.search(r'<a href="([^"]+)">([^<]+)</a>', paragraph).groups()
        assert href.startswith(build.BOOK_URL)
        assert not label.startswith("https://")

    assert build.linkify('See (https://example.com/?a=1&b=2). <tag>') == (
        'See (<a href="https://example.com/?a=1&amp;b=2">'
        'https://example.com/?a=1&amp;b=2</a>). &lt;tag&gt;'
    )


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
