"""Load and validate scenario definitions from YAML files.

Scenario files hold a top-level ``scenarios`` list. The scenario schema is a
placeholder for a future decomposition engine; see
``at1radar.domain.scenarios``.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from at1radar.data.yaml_io import read_yaml
from at1radar.domain.scenarios import Scenario

DEFAULT_SCENARIOS_FILE = Path("data") / "scenarios" / "basic_scenarios.yaml"
"""Default scenario file, relative to the current working directory."""


class ScenarioLoadError(ValueError):
    """Raised when a scenario YAML file cannot be read or validated."""


def load_scenarios(path: Path = DEFAULT_SCENARIOS_FILE) -> list[Scenario]:
    """Load and validate all scenarios in a YAML file."""
    raw = read_yaml(path, error_cls=ScenarioLoadError, kind="scenario")
    if not isinstance(raw, dict) or not isinstance(raw.get("scenarios"), list):
        raise ScenarioLoadError(f"{path}: expected a mapping with a top-level 'scenarios' list")

    scenarios: list[Scenario] = []
    for index, entry in enumerate(raw["scenarios"]):
        try:
            scenarios.append(Scenario.model_validate(entry))
        except ValidationError as exc:
            raise ScenarioLoadError(f"invalid scenario at index {index} in {path}:\n{exc}") from exc

    seen: set[str] = set()
    duplicates: set[str] = set()
    for scenario in scenarios:
        if scenario.name in seen:
            duplicates.add(scenario.name)
        else:
            seen.add(scenario.name)
    if duplicates:
        raise ScenarioLoadError(f"duplicate scenario names in {path}: {sorted(duplicates)}")
    return scenarios
