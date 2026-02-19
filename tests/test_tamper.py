import json
from copy import deepcopy
from pathlib import Path

from veip_verifier_core.schema import validate_evidence_pack
from veip_verifier_core.replay import verify_integrity_binding

FIXTURE = Path(__file__).parent / "fixture_pack.json"


def test_replay_detects_tamper_binding_mismatch():
    pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_evidence_pack(pack)

    # tamper a schema-valid field
    tampered = deepcopy(pack)
    tampered["policy"]["policy_version"] = tampered["policy"]["policy_version"] + "-tampered"

    validate_evidence_pack(tampered)
    res = verify_integrity_binding(tampered, require_binding=True)

    assert res.ok is False
    assert res.reason == "binding mismatch"
    assert res.expected is not None
    assert res.got is not None
    assert res.expected != res.got
