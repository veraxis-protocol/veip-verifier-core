import copy
import json
from pathlib import Path

import pytest

from veip_verifier_core.schema import validate_evidence_pack
from veip_verifier_core.replay import verify_integrity_binding


def load_fixture():
    p = Path("tests/fixture_pack.json")
    return json.loads(p.read_text(encoding="utf-8"))


def test_replay_detects_tamper():
    pack = load_fixture()
    validate_evidence_pack(pack)

    tampered = copy.deepcopy(pack)
    tampered["decision"]["reason_code"] = "TAMPERED"

    res = verify_integrity_binding(tampered, require_binding=True)
    assert res.ok is False
    assert res.reason == "binding mismatch"
    assert res.expected is not None
    assert res.got is not None


def test_replay_requires_binding_when_flagged():
    pack = load_fixture()
    validate_evidence_pack(pack)

    # remove binding carrier
    pack = copy.deepcopy(pack)
    pack["execution"]["outcome"]["result_ref"] = "result/demo/ok"

    res = verify_integrity_binding(pack, require_binding=True)
    assert res.ok is False
    assert "missing binding" in res.reason
