# VEIP Verifier Core

Canonical schema validation + deterministic replay verification for VEIP Evidence Packs.

This repository is the **Verifier Core** for the Veraxis Execution Integrity Protocol (VEIP). It provides the reference logic to:

- Validate VEIP Evidence Packs against the canonical schema
- Canonicalize packs deterministically (stable JSON)
- Verify integrity bindings (hashes) and detect tampering
- Produce machine-readable verification outcomes (PASS/FAIL + reason codes)
- Provide a CLI for local and CI integration

It is intentionally minimal and auditable. It is **not** a registry and it is **not** an endorsement mechanism.

## What it does

- `validate`: schema validation against `schemas/veip-evidence-pack.schema.json`
- `replay`: deterministic canonicalization + hash verification (tamper detection)
- `cli`: `veip-verify ...` commands to validate and verify packs

## What it is not

- Not a multi-operator registry (see `veip-registry`)
- Not an “authority issuer” or policy engine
- Not a cryptographic signing service
- Not a certification authority by itself

## Relationship to veip-spec

- The canonical Evidence Pack schema is defined in `veip-spec/schemas/veip-evidence-pack.schema.json`
- This repo vendors that schema into `schemas/` and treats it as authoritative
- Verifier behavior is intended to remain aligned with `veip-spec` versions (see Versioning)

## Quickstart (local)

Python 3.10+

```bash
python -m pip install -e ".[dev]"
make ci

# validate a pack
veip-verify validate tests/fixture_pack.json

# replay/verify tamper detection
veip-verify replay tests/fixture_pack.json
