from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import SchemaValidationError, get_schema_info, load_evidence_pack, validate_evidence_pack
from .replay import verify_integrity_binding


EXIT_OK = 0
EXIT_FAIL = 2
EXIT_ERROR = 3


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _print_pass(msg: str, quiet: bool) -> None:
    if not quiet:
        print(msg)


def cmd_schema(*, as_json: bool) -> int:
    info = get_schema_info()
    if as_json:
        payload = {"schema_path": str(info.path), "schema_sha256": info.sha256}
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
        return EXIT_OK

    print(str(info.path))
    print(info.sha256)
    return EXIT_OK


def cmd_validate(path: Path, *, quiet: bool) -> int:
    try:
        pack = load_evidence_pack(path)
    except FileNotFoundError:
        eprint(f"ERROR: file not found: {path}")
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        eprint(f"ERROR: invalid JSON: {e}")
        return EXIT_ERROR
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR

    try:
        validate_evidence_pack(pack)
    except SchemaValidationError as e:
        eprint(f"FAIL schema: {e}")
        return EXIT_FAIL
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR

    _print_pass("PASS schema", quiet)
    return EXIT_OK


def cmd_replay(path: Path, *, require_binding: bool, quiet: bool) -> int:
    try:
        pack = load_evidence_pack(path)
    except FileNotFoundError:
        eprint(f"ERROR: file not found: {path}")
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        eprint(f"ERROR: invalid JSON: {e}")
        return EXIT_ERROR
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR

    # Always enforce schema-validity before replay.
    try:
        validate_evidence_pack(pack)
    except SchemaValidationError as e:
        eprint(f"FAIL schema: {e}")
        return EXIT_FAIL
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR

    try:
        res = verify_integrity_binding(pack, require_binding=require_binding)
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR

    if res.ok:
        _print_pass(f"PASS replay: {res.reason}", quiet)
        return EXIT_OK

    eprint(f"FAIL replay: {res.reason}")
    if res.expected is not None:
        eprint(f" expected: {res.expected}")
    if res.got is not None:
        eprint(f" got     : {res.got}")
    return EXIT_FAIL


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="veip-verify",
        description="VEIP Verifier Core (v0.1.x): schema validation + integrity replay.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress PASS output (FAIL/ERROR still printed to stderr).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp_schema = sub.add_parser("schema", help="Print schema path and schema SHA256.")
    sp_schema.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON: {schema_path, schema_sha256}.",
    )

    sp_validate = sub.add_parser("validate", help="Validate an evidence pack against the VEIP schema.")
    sp_validate.add_argument("path", type=Path, help="Path to a VEIP Evidence Pack JSON file.")

    sp_replay = sub.add_parser(
        "replay",
        help="Replay integrity binding (canonicalization + hash verification).",
    )
    sp_replay.add_argument("path", type=Path, help="Path to a VEIP Evidence Pack JSON file.")
    sp_replay.add_argument(
        "--require-binding",
        action="store_true",
        help="Fail if the binding carrier is missing (execution.outcome.result_ref sha256:<digest>).",
    )

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "schema":
        return cmd_schema(as_json=bool(args.json))

    if args.command == "validate":
        return cmd_validate(args.path, quiet=bool(args.quiet))

    if args.command == "replay":
        return cmd_replay(args.path, require_binding=bool(args.require_binding), quiet=bool(args.quiet))

    eprint("ERROR: unknown command")
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
