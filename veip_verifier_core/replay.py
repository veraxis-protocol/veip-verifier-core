from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    reason: str
    expected: Optional[str] = None
    got: Optional[str] = None


def canonicalize_json(obj: Any) -> bytes:
    """
    Canonical JSON bytes for hashing:
      - sorted keys
      - no extra whitespace
      - UTF-8
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_binding_from_pack(evidence_pack: Dict[str, Any]) -> Optional[str]:
    """
    Carrier for the binding digest (schema-allowed):
      evidence_pack.execution.outcome.result_ref = "sha256:<64-hex>"
    """
    exe = evidence_pack.get("execution")
    if not isinstance(exe, dict):
        return None
    out = exe.get("outcome")
    if not isinstance(out, dict):
        return None
    rr = out.get("result_ref")
    if not isinstance(rr, str):
        return None
    if rr.startswith("sha256:") and len(rr) == len("sha256:") + 64:
        return rr.split("sha256:", 1)[1]
    return None


def _pack_without_binding_carrier(evidence_pack: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a deep-copied pack with the binding carrier removed/blanked so hashing
    does not include the stored digest (prevents self-referential hashes).
    """
    # JSON round-trip is a simple deep copy for dict/list primitives.
    p = json.loads(json.dumps(evidence_pack))

    exe = p.get("execution")
    if isinstance(exe, dict):
        out = exe.get("outcome")
        if isinstance(out, dict) and "result_ref" in out:
            # Keep the field (schema requires it) but blank it deterministically.
            out["result_ref"] = "sha256:" + ("0" * 64)

    return p


def compute_integrity_binding(evidence_pack: Dict[str, Any]) -> str:
    """
    Compute the canonical pack SHA256 over the schema-conformant object,
    excluding the binding carrier field (execution.outcome.result_ref).
    """
    p = _pack_without_binding_carrier(evidence_pack)
    return sha256_hex(canonicalize_json(p))


def verify_integrity_binding(evidence_pack: Dict[str, Any], require_binding: bool = False) -> IntegrityResult:
    """
    Verify that the pack's stored binding matches the computed binding.
    If require_binding=True and no binding is present, verification FAILS.
    """
    got = _extract_binding_from_pack(evidence_pack)
    if got is None:
        if require_binding:
            return IntegrityResult(
                False,
                "missing binding (execution.outcome.result_ref sha256:<digest>)",
                expected=None,
                got=None,
            )
        return IntegrityResult(True, "no binding present (not required)", expected=None, got=None)

    expected = compute_integrity_binding(evidence_pack)
    if got == expected:
        return IntegrityResult(True, "binding matches", expected=expected, got=got)

    return IntegrityResult(False, "binding mismatch", expected=expected, got=got)
