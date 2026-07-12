"""Tests for YAML instrument loading and error reporting."""

from __future__ import annotations

from pathlib import Path

import pytest

from at1radar.data.instrument_loader import (
    InstrumentLoadError,
    load_instrument,
    load_instruments,
)
from tests.conftest import FIXTURES_DIR


def test_repo_sample_instruments_load(repo_instruments_dir: Path) -> None:
    instruments = load_instruments(repo_instruments_dir)
    ids = {i.instrument_id for i in instruments}
    assert ids == {"synthetic-alpha", "synthetic-beta"}
    assert all(i.is_synthetic for i in instruments)


def test_load_single_valid_fixture() -> None:
    instrument = load_instrument(FIXTURES_DIR / "valid_instrument.yaml")
    assert instrument.instrument_id == "fixture-valid"


def test_malformed_yaml_reports_path() -> None:
    path = FIXTURES_DIR / "malformed.yaml"
    with pytest.raises(InstrumentLoadError, match=r"malformed YAML.*malformed\.yaml"):
        load_instrument(path)


def test_invalid_field_values_report_path() -> None:
    path = FIXTURES_DIR / "invalid_negative_notional.yaml"
    with pytest.raises(InstrumentLoadError, match=r"invalid_negative_notional\.yaml"):
        load_instrument(path)


def test_non_mapping_yaml_rejected() -> None:
    with pytest.raises(InstrumentLoadError, match="expected a mapping"):
        load_instrument(FIXTURES_DIR / "not_a_mapping.yaml")


def test_missing_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(InstrumentLoadError, match="not found"):
        load_instrument(tmp_path / "does_not_exist.yaml")


def test_directory_passed_as_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(InstrumentLoadError, match="cannot read instrument file"):
        load_instrument(tmp_path)


def test_invalid_utf8_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(InstrumentLoadError, match="cannot read instrument file"):
        load_instrument(path)


def test_missing_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(InstrumentLoadError, match="directory not found"):
        load_instruments(tmp_path / "nowhere")


def test_empty_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(InstrumentLoadError, match="no instrument YAML files"):
        load_instruments(tmp_path)


def test_duplicate_instrument_ids_rejected(tmp_path: Path) -> None:
    source = (FIXTURES_DIR / "valid_instrument.yaml").read_text(encoding="utf-8")
    (tmp_path / "a.yaml").write_text(source, encoding="utf-8")
    (tmp_path / "b.yaml").write_text(source, encoding="utf-8")
    with pytest.raises(InstrumentLoadError, match="duplicate instrument_id"):
        load_instruments(tmp_path)
