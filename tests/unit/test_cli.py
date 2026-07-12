"""End-to-end tests for the CLI against the repository sample data."""

from __future__ import annotations

from pathlib import Path

import pytest

from at1radar.cli import main
from tests.conftest import REPO_ROOT

INSTRUMENTS_DIR = str(REPO_ROOT / "data" / "instruments")
SCENARIOS_FILE = str(REPO_ROOT / "data" / "scenarios" / "basic_scenarios.yaml")


def test_validate_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--instruments-dir",
            INSTRUMENTS_DIR,
            "validate",
            "--scenarios-file",
            SCENARIOS_FILE,
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "2 instrument(s) validated" in captured.out
    assert "4 scenario(s) validated" in captured.out


def test_list_instruments(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--instruments-dir", INSTRUMENTS_DIR, "list-instruments"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "synthetic-alpha" in captured.out
    assert "synthetic-beta" in captured.out


def test_price_prints_both_states(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--instruments-dir",
            INSTRUMENTS_DIR,
            "price",
            "--instrument",
            "synthetic-alpha",
            "--valuation-date",
            "2025-06-30",
            "--discount-rate",
            "0.08",
            "--reset-rate",
            "0.03",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "called_at_first_call" in captured.out
    assert "extended_to_next_call" in captured.out
    assert "% of notional" in captured.out


def test_price_unknown_instrument_fails(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--instruments-dir",
            INSTRUMENTS_DIR,
            "price",
            "--instrument",
            "does-not-exist",
            "--valuation-date",
            "2025-06-30",
            "--discount-rate",
            "0.08",
            "--reset-rate",
            "0.03",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown instrument" in captured.err


def test_price_non_finite_rate_fails(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--instruments-dir",
            INSTRUMENTS_DIR,
            "price",
            "--instrument",
            "synthetic-alpha",
            "--valuation-date",
            "2025-06-30",
            "--discount-rate",
            "nan",
            "--reset-rate",
            "0.03",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "flat_discount_rate must be finite" in captured.err


def test_validate_missing_dir_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--instruments-dir",
            str(tmp_path / "missing"),
            "validate",
            "--scenarios-file",
            SCENARIOS_FILE,
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error:" in captured.err
