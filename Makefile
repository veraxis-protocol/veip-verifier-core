SHELL := /bin/bash
.PHONY: help check test ci

help:
@echo "Targets:"
@echo "  make check  - basic structural + schema checks"
@echo "  make test   - run unit tests"
@echo "  make ci     - check + test"

check:
@set -euo pipefail; \
req=(README.md LICENSE.md pyproject.toml veip_verifier_core/cli.py veip_verifier_core/schema.py veip_verifier_core/replay.py veip_verifier_core/schemas/veip-evidence-pack.schema.json tests/fixture_pack.json); \
for f in "$${req[@]}"; do \
  if [[ ! -f "$$f" ]]; then echo "Missing required file: $$f"; exit 1; fi; \
done; \
python - <<'PY' \
import json, pathlib \
p = pathlib.Path("veip_verifier_core/schemas/veip-evidence-pack.schema.json") \
json.loads(p.read_text(encoding="utf-8")) \
print("OK: schema JSON parses") \
PY
@echo "OK: checks passed"

test:
@pytest -q

ci: check test
