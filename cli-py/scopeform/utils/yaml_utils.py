from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCOPEFORM_YML_PATH = Path("scopeform.yml")


def write_scopeform_yaml(data: dict[str, Any], path: Path = SCOPEFORM_YML_PATH) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def read_scopeform_yaml(path: Path = SCOPEFORM_YML_PATH) -> dict[str, Any]:
    contents = yaml.safe_load(path.read_text(encoding="utf-8"))
    return contents or {}
