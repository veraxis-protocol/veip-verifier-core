from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixture_pack.json"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "veip_verifier_core.cli", *args],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
    )


def test_cli_schema_exit_0():
    p = run_cmd("schema")
    assert p.returncode == 0
    assert "veip-evidence-pack.schema.json" in p.stdout
    assert len(p.stdout.strip().splitlines()) >= 2  # path + sha256


def test_cli_validate_pass_exit_0():
    p = run_cmd("validate", str(FIXTURE))
    assert p.returncode == 0
    assert "PASS schema" in p.stdout


def test_cli_validate_fail_exit_2(tmp_path: Path):
    bad = tmp_path / "bad.json"
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    d["schema_version"] = "999.0.0"
    bad.write_text(json.dumps(d), encoding="utf-8")

    p = run_cmd("validate", str(bad))
    assert p.returncode == 2
    assert "FAIL schema" in p.stderr


def test_cli_replay_pass_exit_0():
    p = run_cmd("replay", str(FIXTURE))
    assert p.returncode == 0
    assert "PASS replay" in p.stdout


def test_cli_missing_file_exit_3(tmp_path: Path):
    missing = tmp_path / "missing.json"
    p = run_cmd("validate", str(missing))
    assert p.returncode == 3
    assert "file not found" in p.stderr.lower()
