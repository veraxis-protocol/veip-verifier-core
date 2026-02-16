from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from veip_verifier_core.schema import (
    SchemaValidationError,
    get_schema_info,
    load_schema,
    validate_evidence_pack,
)
from veip_verifier_core.replay import verify_integrity_binding

# Exit codes (stable contract)
EXIT_OK = 0
EXIT_FAIL = 2
EXIT_ERROR = 3


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise RuntimeError(f"file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid JSON: {path}: {e}") from e

    if not isinstance(data, dict):
        raise RuntimeError(f"evidence pack must be a JSON object at top-level: {path}")
    return data


def cmd_validate(path: Path, quiet: bool = False) -> int:
    pack = _read_json(path)
    try:
        validate_evidence_pack(pack)
    except SchemaValidationError as e:
        if not quiet:
            print(f"FAIL schema: {e}", file=sys.stderr)
        return EXIT_FAIL

    if not quiet:
        print("PASS schema")
    return EXIT_OK


def cmd_replay(path: Path, require_binding: bool = True, quiet: bool = False) -> int:
    pack = _read_json(path)

    # Enforce schema validation before replay (deterministic surface)
    try:
        validate_evidence_pack(pack)
    except SchemaValidationError as e:
        if not quiet:
            print(f"FAIL schema: {e}", file=sys.stderr)
        return EXIT_FAIL

    res = verify_integrity_binding(pack, require_binding=require_binding)
    if res.ok:
        if not quiet:
            print("PASS replay:", res.reason)
        return EXIT_OK

    if not quiet:
        print("FAIL replay:", res.reason, file=sys.stderr)
        if res.expected is not None or res.got is not None:
            print(f"  expected: {res.expected}", file=sys.stderr)
            print(f"  got     : {res.got}", file=sys.stderr)
    return EXIT_FAIL


def cmd_schema(json_out: bool = False) -> int:
    info = get_schema_info()
    if json_out:
        print(json.dumps({"path": str(info.path), "sha256": info.sha256}, indent=2))
    else:
        print(str(info.path))
        print(info.sha256)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="veip-verify",
        description="VEIP Verifier Core (v0.1.x): schema validation + integrity replay.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate an evidence pack against the VEIP schema.")
    p_val.add_argument("path", type=Path, help="Path to evidence pack JSON file.")
    p_val.add_argument("-q", "--quiet", action="store_true", help="No stdout on success.")
    p_val.set_defaults(_fn="validate")

    p_rep = sub.add_parser("replay", help="Replay integrity binding (canonicalization + hash verification).")
    p_rep.add_argument("path", type=Path, help="Path to evidence pack JSON file.")
    p_rep.add_argument("--no-require-binding", action="store_true",
                       help="Treat missing binding as PASS (still validates schema).")
    p_rep.add_argument("-q", "--quiet", action="store_true", help="No stdout on success.")
    p_rep.set_defaults(_fn="replay")

    p_sch = sub.add_parser("schema", help="Print schema path and schema SHA256.")
    p_sch.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    p_sch.set_defaults(_fn="schema")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args._fn == "validate":
            return cmd_validate(args.path, quiet=args.quiet)

        if args._fn == "replay":
            require_binding = not args.no_require_binding
            return cmd_replay(args.path, require_binding=require_binding, quiet=args.quiet)

        if args._fn == "schema":
            return cmd_schema(json_out=args.json)

        # Should be unreachable because argparse enforces required subcommand
        raise RuntimeError("unknown command")

    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
