"""Shared YAML reading helpers for instrument and scenario loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_yaml(path: Path, *, error_cls: type[Exception], kind: str) -> Any:
    """Read a YAML file, wrapping I/O and parse errors in ``error_cls``.

    ``kind`` is a short noun used in error messages (e.g. ``"instrument"``).
    """
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise error_cls(f"{kind} file not found: {path}") from exc
    except (OSError, UnicodeError) as exc:
        raise error_cls(f"cannot read {kind} file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise error_cls(f"malformed YAML in {path}: {exc}") from exc
