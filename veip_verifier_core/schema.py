from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import Draft202012Validator


# Canonical vendored schema location (kept inside the package for reliability).
_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "veip-evidence-pack.schema.json"


class SchemaLoadError(RuntimeError):
    pass


class SchemaValidationError(ValueError):
    """Raised when an evidence pack fails JSON Schema validation."""


@dataclass(frozen=True)
class SchemaInfo:
    path: Path
    sha256: str


def load_schema_path() -> Path:
    """Return the on-disk path of the vendored VEIP Evidence Pack schema."""
    return _SCHEMA_PATH


def load_schema() -> Dict[str, Any]:
    """Load the vendored VEIP Evidence Pack JSON Schema."""
    p = load_schema_path()
    if not p.exists():
        raise SchemaLoadError(
            f"Missing schema file at {p}. "
            f"Expected vendored schema at veip_verifier_core/schemas/veip-evidence-pack.schema.json"
        )
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SchemaLoadError(f"Failed to parse schema JSON at {p}: {e}") from e


def schema_sha256(schema_path: Optional[Path] = None) -> str:
    """Compute SHA256 of the schema bytes (used for binding / reproducibility)."""
    import hashlib

    p = schema_path or load_schema_path()
    if not p.exists():
        raise SchemaLoadError(f"Missing schema file at {p}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def get_schema_info() -> SchemaInfo:
    """Return schema path and SHA256."""
    p = load_schema_path()
    return SchemaInfo(path=p, sha256=schema_sha256(p))


def validate_evidence_pack(evidence_pack: Dict[str, Any], *, schema: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate a VEIP Evidence Pack against the canonical JSON Schema.

    Raises:
        SchemaValidationError: if validation fails (message includes the first error).
        SchemaLoadError: if schema is missing/unparseable.
    """
    sch = schema or load_schema()
    try:
        Draft202012Validator(sch).validate(evidence_pack)
    except Exception as e:
        # jsonschema raises jsonschema.exceptions.ValidationError
        raise SchemaValidationError(str(e)) from e


def validate_evidence_pack_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON text, validate as an Evidence Pack, and return the parsed object.
    """
    try:
        obj = json.loads(text)
    except Exception as e:
        raise SchemaValidationError(f"Invalid JSON: {e}") from e
    if not isinstance(obj, dict):
        raise SchemaValidationError("Evidence Pack must be a JSON object.")
    validate_evidence_pack(obj)
    return obj
