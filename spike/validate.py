"""Validate a composition against its target vocab schema (core.schema.json + target overlay).

Usage: .venv/bin/python validate.py composition-pptx.json pptx.schema.json
"""
import json
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).parent


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    comp_path, schema_path = sys.argv[1], sys.argv[2]
    composition = load(comp_path)
    schema = load(schema_path)
    core = load("core.schema.json")

    # Resolve the allOf[0] $ref to core.schema.json by inlining it directly —
    # this spike keeps the two files physically separate (as the real registry
    # would: core.schema.json + a DS's schema/overrides.json per §6.2) but
    # validates the composed result in one pass rather than standing up a
    # full $id-based resolver for a two-file spike.
    schema["allOf"][0] = core
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)

    errors = sorted(validator.iter_errors(composition), key=str)
    if errors:
        print(f"INVALID  {comp_path} against {schema_path}")
        for e in errors:
            print(f"  - {list(e.path)}: {e.message}")
        sys.exit(1)
    print(f"VALID    {comp_path} against {schema_path}")


if __name__ == "__main__":
    main()
