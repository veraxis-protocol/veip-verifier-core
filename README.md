# VEIP Verifier Core (Reference)

Verifier Core for the Veraxis Execution Integrity Protocol (VEIP): schema validation + deterministic replay checks for VEIP Evidence Packs.

This repository is a minimal, operator-neutral reference implementation of “verification” logic. It does not provide certification, endorsement, or registry services.

## What it does

- Validates a VEIP Evidence Pack against the canonical JSON Schema (`schemas/veip-evidence-pack.schema.json`)
- Performs deterministic replay checks (canonicalization + hash binding) for tamper detection
- Exposes both:
  - a Python API (`veip_verifier_core`)
  - a CLI (`veip-verifier-core`)

## What it is not

- Not a certification authority
- Not a registry / storage system
- Not a supervisory endorsement mechanism
- Not a production “attestation” service (no keys, signing, timestamping)

## Inputs / Outputs

Input: a VEIP Evidence Pack JSON document.

Output:
- `PASS` if schema-valid and replay-valid
- `FAIL` with a precise reason if invalid

## Quickstart

Python 3.10+

```bash
python -m pip install -e ".[dev]"
make ci
