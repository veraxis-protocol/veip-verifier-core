from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Tuple


class ReplayError(ValueError):
    pass


def _canonical_json_bytes(obj: Any) -> bytes:
    """
    Canonical JSON encoding:
    - UTF-8
    - sorted keys
    - no insignificant whitespace
    - stable for hashing
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonicalize_for_binding(evidence_pack: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
    """
    Produce the canonical bytes used for integrity binding.
    Strategy:
      - Copy pack
      - Remove existing execution.integrity and any derived digest fields if present
      - Hash the rest deterministically
    """
    if not isinstance(evidence_pack, dict):
        raise ReplayError("Evidence Pack must be an object.")

    pack = json.loads(json.dumps(evidence_pack))  # deep copy via JSON-safe roundtrip

    # Remove integrity block before hashing (it is self-referential).
    exec_block = pack.get("execution")
    if isinstance(exec_block, dict):
        exec_block.pop("integrity", None)

    # Optionally remove top-level derived fields if present in future versions
    pack.pop("integrity", None)

    b = _canonical_json_bytes(pack)
    return b, pack


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    expected: str
    computed: str
    reason: str


def compute_integrity_binding(evidence_pack: Dict[str, Any]) -> str:
    b, _ = canonicalize_for_binding(evidence_pack)
    return sha256_hex(b)


def verify_integrity_binding(evidence_pack: Dict[str, Any]) -> IntegrityResult:
    """
    Verify execution.integrity.pack_sha256 against the canonicalized Evidence Pack hash.
    Expected shape:
      execution: { integrity: { pack_sha256: <hex> , computed_at?: <iso8601> } }
    """
    exec_block = evidence_pack.get("execution")
    if not isinstance(exec_block, dict):
        return IntegrityResult(False, expected="", computed="", reason="missing execution block")

    integrity = exec_block.get("integrity")
    if not isinstance(integrity, dict):
        return IntegrityResult(False, expected="", computed="", reason="missing execution.integrity block")

    expected = integrity.get("pack_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        return IntegrityResult(False, expected=str(expected), computed="", reason="missing/invalid integrity.pack_sha256")

    computed = compute_integrity_binding(evidence_pack)

    if computed != expected:
        return IntegrityResult(False, expected=expected, computed=computed, reason="hash mismatch")

    return IntegrityResult(True, expected=expected, computed=computed, reason="ok")


def attach_integrity_binding(evidence_pack: Dict[str, Any], *, computed_at: str | None = None) -> Dict[str, Any]:
    """
    Attach execution.integrity.pack_sha256 to a pack (mutates a copy, returns new dict).
    """
    pack = json.loads(json.dumps(evidence_pack))
    pack.setdefault("execution", {})
    if not isinstance(pack["execution"], dict):
        raise ReplayError("execution must be an object")
    pack["execution"].setdefault("integrity", {})
    if not isinstance(pack["execution"]["integrity"], dict):
        raise ReplayError("execution.integrity must be an object")

    digest = compute_integrity_binding(pack)
    pack["execution"]["integrity"]["pack_sha256"] = digest
    pack["execution"]["integrity"]["computed_at"] = computed_at or datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return pack
