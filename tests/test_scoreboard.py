from datetime import date, timedelta
from html import escape
import json
from pathlib import Path
import sys
import tempfile
from xml.etree import ElementTree

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scoreboard import render_scoreboard
from traps import TRAPS


@pytest.fixture
def scoreboard_temp():
    with tempfile.TemporaryDirectory(prefix="cc-scoreboard-test-") as directory:
        yield Path(directory)


def test_scoreboard_renders_results_and_caps_history(scoreboard_temp):
    results = [
        {"id": "t01", "status": "REPRODUCED", "detail": None},
        {"id": "t02", "status": "NOT REPRODUCED", "detail": None},
        {"id": "t04", "status": "CANNOT CHECK", "detail": "Missing <tool> & dependency"},
    ]
    results_path = scoreboard_temp / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")
    environment = {
        "runner_image": "win25 20261122.1",
        "windows_version": "10.0.26100",
        "powershell_version": "5.1.26100.1",
        "python_version": "3.13.1",
        "locale": "en-US",
        "oem_code_page": 437,
    }
    first_date = date(2024, 1, 1)
    previous = [
        {"date": (first_date + timedelta(weeks=week)).isoformat(), "reproduced": 1, "total": 3}
        for week in range(104)
    ]
    output_dir = scoreboard_temp / "docs" / "scoreboard"
    output_dir.mkdir(parents=True)
    history_path = output_dir / "history.json"
    history_path.write_text(json.dumps(previous), encoding="utf-8")

    run_date = "2025-12-29"
    render_scoreboard(results_path, output_dir, environment, run_date)

    assert {p.name for p in output_dir.iterdir()} == {
        "latest.json", "history.json", "badge.svg", "index.html", "ja.html",
    }
    summary = {"date": run_date, "reproduced": 1, "total": 3}
    assert json.loads(history_path.read_text(encoding="utf-8")) == previous[1:] + [summary]
    assert json.loads((output_dir / "latest.json").read_text(encoding="utf-8")) == {
        **summary, "environment": environment, "results": results,
    }
    badge = ElementTree.parse(output_dir / "badge.svg").getroot()
    assert badge.attrib["aria-label"] == "windows traps | 1/3 reproduce"
    assert [part.text for part in badge.findall(".//{http://www.w3.org/2000/svg}text")] == [
        "windows traps", "1/3 reproduce",
    ]
    t01 = next(trap for trap in TRAPS if trap["id"] == "t01")
    for lang, filename, status in (("en", "index.html", "REPRODUCED"), ("ja", "ja.html", "起きる")):
        page = (output_dir / filename).read_text(encoding="utf-8")
        assert f'<html lang="{lang}">' in page
        assert f'<a href="../{lang}/t01.html">{escape(t01[lang]["title"])}</a>' in page
        assert f"<strong>{status}</strong>" in page
        assert "Missing &lt;tool&gt; &amp; dependency" in page
        for value in (run_date, *environment.values()):
            assert str(value) in page
