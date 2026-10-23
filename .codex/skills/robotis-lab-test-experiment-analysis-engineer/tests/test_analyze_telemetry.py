"""Pytest tests for example offline analyzer — synthetic fixtures, NOT Webots evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_telemetry import summarize


def fixture_run(tmp_path, *, rows=None, source_sha="a" * 40):
    p = tmp_path / "test.csv"
    m = tmp_path / "test.json"
    rows = rows or [
        {"run_id": "synthetic-1", "t_s": 0.0, "roll_rad": 0.01, "pitch_rad": 0.0,
         "state": "STAND", "root_x_m": 0.0, "root_z_m": 0.0},
        {"run_id": "synthetic-1", "t_s": 0.1, "roll_rad": 0.02, "pitch_rad": -0.01,
         "state": "STAND", "root_x_m": 0.001, "root_z_m": 0.002},
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    m.write_text(json.dumps({
        "run_id": "synthetic-1", "source_commit_sha": source_sha,
        "webots_version": "Webots R2025a", "result": "controller_exited",
        "config_sha256": "b" * 64, "world_sha256": "c" * 64,
        "notes": "SYNTHETIC MOCK UNIT FIXTURE; not native Webots output"
    }), encoding="utf-8")
    return p, m


def test_valid_mock_data_never_scientific_pass(tmp_path):
    p, m = fixture_run(tmp_path)
    report = summarize(p, m)
    assert report["data_integrity"] == "PASS"
    assert report["pass_fail_status"] == "INCONCLUSIVE"
    assert report["scientific_acceptance"] == "INCONCLUSIVE"
    assert report["native_contact_verified"] is None
    assert report["metrics"]["rows"] == 2
    assert report["metrics"]["max_root_planar_drift_m"] == pytest.approx(0.00223607)


@pytest.mark.parametrize("bad_value", ["nan", "inf", "-inf", "bad", ""])
def test_nonfinite_or_invalid_telemetry_withholds_metrics(tmp_path, bad_value):
    p, m = fixture_run(tmp_path)
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("0.02", bad_value), encoding="utf-8")
    report = summarize(p, m)
    assert report["data_integrity"] == "INCONCLUSIVE"
    assert report["pass_fail_status"] == "INCONCLUSIVE"
    assert report["metrics"] == {}


def test_duplicate_timestamp_invalidates_data(tmp_path):
    p, m = fixture_run(tmp_path)
    p.write_text(p.read_text(encoding="utf-8").replace("0.1,0.02", "0.0,0.02"), encoding="utf-8")
    report = summarize(p, m)
    assert "non_monotonic_or_duplicate_timestamps" in report["errors"]


def test_missing_provenance_is_inconclusive(tmp_path):
    p, m = fixture_run(tmp_path, source_sha="unknown")
    r = summarize(p, m)
    assert "missing_verified_git_commit" in r["errors"]
    assert r["pass_fail_status"] == "INCONCLUSIVE"


def test_fault_is_fail_if_artifact_valid(tmp_path):
    p, m = fixture_run(tmp_path)
    p.write_text(p.read_text(encoding="utf-8").replace("STAND,0.001", "FAULT,0.001"), encoding="utf-8")
    r = summarize(p, m)
    assert r["data_integrity"] == "PASS"
    assert r["pass_fail_status"] == "FAIL"
    assert r["metrics"]["first_fault_t_s"] == pytest.approx(0.1)


def test_metadata_run_id_mismatch(tmp_path):
    p, m = fixture_run(tmp_path)
    metadata = json.loads(m.read_text(encoding="utf-8"))
    metadata["run_id"] = "other"
    m.write_text(json.dumps(metadata), encoding="utf-8")
    r = summarize(p, m)
    assert "metadata_run_id_mismatch" in r["errors"]


def test_missing_file_not_auto_pass(tmp_path):
    r = summarize(tmp_path / "absent.csv")
    assert r["metrics"] == {}
    assert r["pass_fail_status"] == "INCONCLUSIVE"
    assert any(e.startswith("cannot_read_csv") for e in r["errors"])
