"""Load and validate AT1 instrument definitions from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from at1radar.domain.instruments import AT1Instrument

DEFAULT_INSTRUMENTS_DIR = Path("data") / "instruments"
"""Default instruments directory, relative to the current working directory."""


class InstrumentLoadError(ValueError):
    """Raised when an instrument YAML file cannot be read or validated."""


def load_instrument(path: Path) -> AT1Instrument:
    """Load and validate a single instrument YAML file.

    Raises :class:`InstrumentLoadError` with the offending path in the
    message if the file is missing, is not valid YAML, is not a mapping, or
    fails domain validation.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InstrumentLoadError(f"instrument file not found: {path}") from exc
    except (OSError, UnicodeError) as exc:
        raise InstrumentLoadError(f"cannot read instrument file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise InstrumentLoadError(f"malformed YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise InstrumentLoadError(
            f"{path}: expected a mapping of instrument fields, got {type(raw).__name__}"
        )
    try:
        return AT1Instrument.model_validate(raw)
    except ValidationError as exc:
        raise InstrumentLoadError(f"invalid instrument in {path}:\n{exc}") from exc


def load_instruments(directory: Path = DEFAULT_INSTRUMENTS_DIR) -> list[AT1Instrument]:
    """Load all ``*.yaml`` instrument files in a directory, sorted by filename.

    Raises :class:`InstrumentLoadError` if the directory does not exist,
    contains no YAML files, contains an invalid file, or contains duplicate
    ``instrument_id`` values.
    """
    if not directory.is_dir():
        raise InstrumentLoadError(f"instruments directory not found: {directory}")
    files = sorted(directory.glob("*.yaml"))
    if not files:
        raise InstrumentLoadError(f"no instrument YAML files found in {directory}")

    instruments = [load_instrument(path) for path in files]
    seen: dict[str, Path] = {}
    for instrument, path in zip(instruments, files, strict=True):
        if instrument.instrument_id in seen:
            raise InstrumentLoadError(
                f"duplicate instrument_id '{instrument.instrument_id}' in "
                f"{path} (already defined in {seen[instrument.instrument_id]})"
            )
        seen[instrument.instrument_id] = path
    return instruments
