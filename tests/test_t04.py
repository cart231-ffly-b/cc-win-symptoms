import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from traps import TRAPS


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PowerShell 5.1")
def test_t04_reproduces_question_marks_with_utf8_bom():
    source = next(trap["check"] for trap in TRAPS if trap["id"] == "t04")
    assert (ROOT / "checks" / "t04.ps1").read_text(encoding="ascii") == source + "\n"
    with tempfile.TemporaryDirectory(prefix="cc-t04-test-") as folder:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "[Console]::InputEncoding = [Text.Encoding]::UTF8; "
             "& powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'checks/t04.ps1'"],
            cwd=ROOT, env={**os.environ, "TEMP": folder}, capture_output=True, text=True, check=True,
        )

    *_, byte_line, status = result.stdout.splitlines()
    assert byte_line.startswith("bytes=efbbbf3f3f ")
    assert status == "REPRODUCED"
