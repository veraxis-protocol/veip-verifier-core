# VEIP Verifier Core

Canonical schema validation and deterministic replay verification for VEIP Evidence Packs.

The VEIP Verifier Core is the reference verification engine for the Veraxis Execution Integrity Protocol (VEIP). It validates Evidence Packs against the canonical schema and performs deterministic replay checks to detect tampering or structural nonconformance.

This repository defines the verification surface. It does not define certification, registry governance, or supervisory endorsement.

---

## Purpose

The Verifier Core provides:

- Schema validation against the canonical VEIP Evidence Pack schema  
- Deterministic canonicalization of Evidence Packs  
- Integrity binding verification (hash verification / tamper detection)  
- Machine-readable verification outcomes (PASS / FAIL with reason codes)  
- A stable CLI interface for local and CI integration  

The implementation is intentionally minimal, auditable, and reproducible.

---

## What this repository is not

This repository is not:

- A multi-operator registry (see `veip-registry`)  
- A supervisory endorsement authority  
- A certification body  
- A production WORM storage system  
- A policy execution engine  

It is strictly a verifier.

---

## Relationship to veip-spec

The canonical Evidence Pack schema is defined in:

```

veip-spec/schemas/veip-evidence-pack.schema.json

```

This repository vendors that schema into:

```

schemas/veip-evidence-pack.schema.json

````

The schema in this repository is treated as authoritative for verification logic.

Verifier Core versions must remain aligned with `veip-spec` schema versions.

---

## Quickstart (Local Development)

Python 3.10+

Install:

```bash
python -m pip install -e ".[dev]"
make ci
````

Validate an Evidence Pack:

```bash
veip-verify validate tests/fixture_pack.json
```

Replay and verify integrity bindings:

```bash
veip-verify replay tests/fixture_pack.json
```

Print schema information:

```bash
veip-verify schema
```

---

## CLI Contract (Stable Surface)

Initial CLI version: `v0.1.0`

### Commands

* `veip-verify validate <path>`
  Perform schema validation against the canonical VEIP schema.

* `veip-verify replay <path>`
  Canonicalize the Evidence Pack and verify integrity bindings.

* `veip-verify schema`
  Print schema path and schema SHA256 fingerprint.

---

## Exit Codes

* `0` — Verification PASS
* `2` — Verification FAIL (invalid, tampered, or nonconformant)
* `3` — Tool/runtime error

Exit codes are stable and part of the public contract.

---

## Versioning

Verifier Core version: `0.1.0`
Aligned VEIP specification version: `0.1.0`

Breaking changes follow semantic versioning and must track schema changes in `veip-spec`.

If the schema changes in a backward-incompatible way, the Verifier Core major version must increment.

---

## Security Model (Minimal Scope)

The Verifier Core assumes:

* The Evidence Pack is provided as a JSON artifact.
* Integrity bindings are deterministic and reproducible.
* Canonicalization is stable across environments.
* The verifier itself is auditable and reproducible from source.

The Verifier Core does not:

* Provide cryptographic signing
* Manage keys
* Issue certificates
* Provide registry-level endorsement

---

## Licensing and Trademark

This repository is released under the VEIP License (see `LICENSE.md`).

Use of terms such as:

* “VEIP Certified”
* “VEIP Compliant”
* “Veraxis, Veraxis Execution Integrity Protocol”

is governed separately by VEIP trademark and registry policy.
This repository does not grant certification status.

---

## Status

Reference implementation — minimal surface, specification-aligned.

Further hardening and conformance test suites are expected in future minor releases.

