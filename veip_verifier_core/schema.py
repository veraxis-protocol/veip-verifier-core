from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SchemaValidationError(Exception):
    """Raised when an evidence pack fails schema validation."""


# ---------------------------------------------------------------------------
# Schema loading + metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SchemaInfo:
    path: Path
    sha256: str


def _schema_path() -> Path:
    return (
        Path(__file__).parent
        / "schemas"
        / "veip-evidence-pack.schema.json"
    )


def _load_schema() -> Dict[str, Any]:
    path = _schema_path()
    if not path.exists():
        raise RuntimeError(f"schema file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_schema_info() -> SchemaInfo:
    """
    Return schema path + SHA256 (for CLI `schema` command).
    """
    path = _schema_path()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    return SchemaInfo(path=path, sha256=digest)


# ---------------------------------------------------------------------------
# Evidence pack loading
# ---------------------------------------------------------------------------

def load_evidence_pack(path: Path) -> Dict[str, Any]:
    """
    Load an evidence pack JSON file from disk.

    Raises:
      - FileNotFoundError if missing
      - json.JSONDecodeError if invalid JSON
      - SchemaValidationError if not a JSON object
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)

    if not isinstance(data, dict):
        raise SchemaValidationError("evidence pack must be a JSON object")

    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_evidence_pack(evidence_pack: Dict[str, Any]) -> None:
    """
    Validate evidence pack against VEIP schema.

    Raises:
      - SchemaValidationError on failure
    """
    schema = _load_schema()
    validator = Draft202012Validator(schema)

    try:
        validator.validate(evidence_pack)
    except Exception as e:
        raise SchemaValidationError(str(e)) from e
