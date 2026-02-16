# veip_verifier_core/cli.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from veip_verifier_core.schema import SchemaValidationError, get_schema_info, validate_evidence_pack
from veip_verifier_core.replay import IntegrityResult, verify_integrity_binding

EXIT_OK = 0
EXIT_FAIL = 2
EXIT_ERROR = 3


def eprint(*args: object, **kwargs: object) -> None:
    print(*args, file=sys.stderr, **kwargs)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e


def cmd_schema(_: argparse.Namespace) -> int:
    info = get_schema_info()
    print(str(info.path))
    print(info.sha256)
    return EXIT_OK


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        pack = _load_json(path)
        validate_evidence_pack(pack)
        print("PASS schema")
        return EXIT_OK
    except SchemaValidationError as e:
        eprint(f"FAIL schema: {e}")
        return EXIT_FAIL
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR


def cmd_replay(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        pack = _load_json(path)

        # Always ensure schema-valid before replay
        validate_evidence_pack(pack)

        res: IntegrityResult = verify_integrity_binding(pack, require_binding=bool(args.require_binding))

        if res.ok:
            print(f"PASS replay: {res.reason}")
            return EXIT_OK

        eprint(f"FAIL replay: {res.reason}")
        if res.expected is not None:
            eprint(f" expected: {res.expected}")
        if res.got is not None:
            eprint(f" got     : {res.got}")
        return EXIT_FAIL

    except SchemaValidationError as e:
        eprint(f"FAIL schema: {e}")
        return EXIT_FAIL
    except Exception as e:
        eprint(f"ERROR: {e}")
        return EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="veip-verify",
        description="VEIP Verifier Core (v0.1.x): schema validation + integrity replay.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate an evidence pack against the VEIP schema.")
    p_validate.add_argument("path", help="Path to evidence pack JSON file.")
    p_validate.set_defaults(func=cmd_validate)

    p_replay = sub.add_parser("replay", help="Replay integrity binding (canonicalization + hash verification).")
    p_replay.add_argument("path", help="Path to evidence pack JSON file.")
    p_replay.add_argument(
        "--require-binding",
        action="store_true",
        help="Fail if no binding is present in execution.outcome.result_ref (sha256:<digest>).",
    )
    p_replay.set_defaults(func=cmd_replay)

    p_schema = sub.add_parser("schema", help="Print schema path and schema SHA256.")
    p_schema.set_defaults(func=cmd_schema)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
