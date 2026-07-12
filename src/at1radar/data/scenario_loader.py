"""Load and validate scenario definitions from YAML files.

Scenario files hold a top-level ``scenarios`` list. The scenario schema is a
placeholder for a future decomposition engine; see
``at1radar.domain.scenarios``.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from at1radar.domain.scenarios import Scenario

DEFAULT_SCENARIOS_FILE = Path("data") / "scenarios" / "basic_scenarios.yaml"
"""Default scenario file, relative to the current working directory."""


class ScenarioLoadError(ValueError):
    """Raised when a scenario YAML file cannot be read or validated."""


def load_scenarios(path: Path = DEFAULT_SCENARIOS_FILE) -> list[Scenario]:
    """Load and validate all scenarios in a YAML file."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScenarioLoadError(f"scenario file not found: {path}") from exc
    except (OSError, UnicodeError) as exc:
        raise ScenarioLoadError(f"cannot read scenario file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ScenarioLoadError(f"malformed YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("scenarios"), list):
        raise ScenarioLoadError(f"{path}: expected a mapping with a top-level 'scenarios' list")

    scenarios: list[Scenario] = []
    for index, entry in enumerate(raw["scenarios"]):
        try:
            scenarios.append(Scenario.model_validate(entry))
        except ValidationError as exc:
            raise ScenarioLoadError(f"invalid scenario at index {index} in {path}:\n{exc}") from exc

    names = [scenario.name for scenario in scenarios]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise ScenarioLoadError(f"duplicate scenario names in {path}: {sorted(duplicates)}")
    return scenarios
