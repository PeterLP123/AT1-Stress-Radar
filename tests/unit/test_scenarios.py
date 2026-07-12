"""Tests for the placeholder scenario schema and loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from at1radar.data.scenario_loader import ScenarioLoadError, load_scenarios
from at1radar.domain.scenarios import CallState, Scenario


def test_repo_scenario_file_validates(repo_scenarios_file: Path) -> None:
    scenarios = load_scenarios(repo_scenarios_file)
    names = [s.name for s in scenarios]
    assert names == ["base_case", "rates_up_100", "credit_repricing_150", "forced_extension"]
    forced = scenarios[-1]
    assert forced.call_assumption is CallState.EXTENDED_TO_NEXT_CALL
    assert forced.issuer_equity_shock == pytest.approx(-0.30)
    assert forced.cet1_ratio_shock == pytest.approx(-0.02)


def test_invalid_call_assumption_rejected() -> None:
    with pytest.raises(ValidationError, match="call_assumption"):
        Scenario.model_validate(
            {
                "name": "bad",
                "description": "invalid call assumption",
                "risk_free_rate_shock_bps": 0,
                "credit_spread_shock_bps": 0,
                "reset_rate_shock_bps": 0,
                "call_assumption": "never_called",
            }
        )


def test_missing_scenarios_key_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("not_scenarios: []\n", encoding="utf-8")
    with pytest.raises(ScenarioLoadError, match="top-level 'scenarios' list"):
        load_scenarios(path)


def test_invalid_scenario_entry_reports_index(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "scenarios:\n  - name: only_name\n    description: missing shock fields\n",
        encoding="utf-8",
    )
    with pytest.raises(ScenarioLoadError, match="index 0"):
        load_scenarios(path)


def test_missing_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScenarioLoadError, match="not found"):
        load_scenarios(tmp_path / "nowhere.yaml")


def test_directory_passed_as_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScenarioLoadError, match="cannot read scenario file"):
        load_scenarios(tmp_path)


def test_invalid_utf8_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ScenarioLoadError, match="cannot read scenario file"):
        load_scenarios(path)


def test_malformed_yaml_rejected(tmp_path: Path) -> None:
    path = tmp_path / "malformed.yaml"
    path.write_text("scenarios: [unclosed\n", encoding="utf-8")
    with pytest.raises(ScenarioLoadError, match="malformed YAML"):
        load_scenarios(path)


def test_duplicate_names_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text(
        """\
scenarios:
  - name: duplicate
    description: first
    risk_free_rate_shock_bps: 0
    credit_spread_shock_bps: 0
    reset_rate_shock_bps: 0
    call_assumption: called_at_first_call
  - name: duplicate
    description: second
    risk_free_rate_shock_bps: 100
    credit_spread_shock_bps: 0
    reset_rate_shock_bps: 100
    call_assumption: called_at_first_call
""",
        encoding="utf-8",
    )
    with pytest.raises(ScenarioLoadError, match="duplicate scenario names"):
        load_scenarios(path)
