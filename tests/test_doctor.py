import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from traps import TRAPS


DOCTOR = ROOT / "docs" / "doctor.ps1"
BASE = "https://cart231-ffly-b.github.io/cc-win-symptoms/"
POWERSHELL = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]


@pytest.fixture(scope="module")
def doctor_source():
    subprocess.run([sys.executable, "build.py"], cwd=ROOT, check=True)
    return DOCTOR.read_text(encoding="ascii")


@pytest.fixture
def doctor_temp():
    with tempfile.TemporaryDirectory(prefix="cc-doctor-test-") as directory:
        yield Path(directory)


def test_doctor_build(doctor_source):
    data = re.search(r"\$traps = @'\n(.*?)\n'@", doctor_source, re.S)[1]
    generated = json.loads(data)
    assert [tr["id"] for tr in generated] == [tr["id"] for tr in TRAPS]

    for row, tr in zip(generated, TRAPS):
        assert row["ja"] == tr["ja"]["title"]
        assert row["en"] == tr["en"]["title"]
        assert row["check"].encode("ascii") == (ROOT / "checks" / f"{tr['id']}.ps1").read_bytes()

    runner = (ROOT / "check.ps1").read_text(encoding="ascii")
    old_claude_list = re.search(r"\$claudeIds = @\(([^\n]+)\)", runner)[1]
    slow_id = re.search(r"\$SkipSlow -and \$id -eq '([^']+)'", runner)[1]
    claude_ids = {tr["id"] for tr in generated if tr["claude"]}
    # check.ps1 lists the original Claude checks. traps.py also flags the later ones.
    assert set(re.findall(r"'([^']+)'", old_claude_list)) <= claude_ids
    assert claude_ids == {tr["id"] for tr in TRAPS if tr.get("claude")}
    assert {tr["id"] for tr in generated if tr["slow"]} == {slow_id}


@pytest.mark.skipif(os.name != "nt", reason="requires Windows PowerShell 5.1")
@pytest.mark.parametrize("lang", ["en", "ja"])
def test_doctor_runs_two_checks(doctor_source, doctor_temp, lang):
    temp = doctor_temp / "temp with spaces"
    temp.mkdir()
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), CCDOCTOR_ALL="",
               CCDOCTOR_ONLY="t01,t02", CCDOCTOR_LANG=lang)

    command = [*POWERSHELL, str(DOCTOR)]
    if lang == "ja":
        wrapper = doctor_temp / "cp932.ps1"
        wrapper.write_text(
            "param($Doctor)\n"
            "[Threading.Thread]::CurrentThread.CurrentUICulture = [cultureinfo]'en-US'\n"
            "[Threading.Thread]::CurrentThread.CurrentCulture = [cultureinfo]'en-US'\n"
            "[Console]::OutputEncoding = [Text.Encoding]::GetEncoding(932)\n"
            "Get-Content -LiteralPath $Doctor -Raw -Encoding ASCII | iex\n",
            encoding="ascii",
        )
        command = [*POWERSHELL, str(wrapper), str(DOCTOR)]

    proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, check=True, timeout=30)
    assert not proc.stderr, proc.stderr
    lines = proc.stdout.decode("cp932" if lang == "ja" else "ascii").splitlines()
    if lang == "ja":
        header = "ID  結果  症状  |  ページ"
        reproduced_label, other_label = "起きる", "起きない"
        summary = "この PC では、調べた 2 件のうち {} 件が起きました。各行のページに直し方があります。"
    else:
        header = "ID  Result  Symptom  |  Page"
        reproduced_label, other_label = "REPRODUCED", "NOT REPRODUCED"
        summary = "{} of 2 checks reproduce on this PC. Each row's page has the fix."

    assert len(lines) == 4, lines
    assert lines[0] == header
    rows = [line.split("  ", 2) for line in lines[1:-1]]
    assert {row[0] for row in rows} == {"t01", "t02"}
    assert rows == sorted(rows, key=lambda row: (row[1] != reproduced_label, row[0]))
    titles = {tr["id"]: tr[lang]["title"] for tr in TRAPS}
    for trap_id, status, title_and_url in rows:
        assert status in (reproduced_label, other_label)
        assert title_and_url == f"{titles[trap_id]}  |  {BASE}{lang}/{trap_id}.html"
    reproduced = sum(status == reproduced_label for _, status, _ in rows)
    assert lines[-1] == summary.format(reproduced)
    assert list(temp.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="requires Windows PowerShell 5.1")
def test_doctor_summarizes_skipped_checks(doctor_source, doctor_temp):
    env = dict(os.environ, TEMP=str(doctor_temp), TMP=str(doctor_temp), CCDOCTOR_ALL="",
               CCDOCTOR_ONLY="t13,t14", CCDOCTOR_LANG="en")
    proc = subprocess.run([*POWERSHELL, str(DOCTOR)], cwd=ROOT, env=env,
                          capture_output=True, check=True, timeout=30)
    assert not proc.stderr, proc.stderr
    assert proc.stdout.decode("ascii").splitlines() == [
        "ID  Result  Symptom  |  Page",
        f"Skipped 1 that would call Claude and count toward your usage. Index: {BASE}en/index.html",
        "To include t13, run $env:CCDOCTOR_ALL='1' before running the doctor again.",
        "0 of 0 checks reproduce on this PC. Each row's page has the fix.",
    ]
