"""CLI — mainPRD R10, M0-spec.md §5."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bindery.ds import loader
from bindery.ds.errors import DesignSystemError
from bindery.render.errors import CompositionError, RenderError
from bindery.render.pptx import render


def _generate(args: argparse.Namespace) -> int:
    composition_path = Path(args.composition)
    composition = json.loads(composition_path.read_text())

    try:
        ds = loader.load(args.ds, root=Path(args.ds_root))
    except DesignSystemError as e:
        print(str(e), file=sys.stderr)
        return 2

    out_path = Path(args.out) / f"{composition_path.stem}.pptx"

    try:
        result = render(composition, ds, out_path)
    except CompositionError as e:
        print(str(e), file=sys.stderr)
        return 3
    except RenderError as e:
        print(str(e), file=sys.stderr)
        return 4

    print(str(result.path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bindery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate", help="Render a hand-authored composition to a .pptx"
    )
    generate.add_argument("composition")
    generate.add_argument("--ds", required=True)
    generate.add_argument("--out", required=True)
    generate.add_argument("--ds-root", default="design-systems")
    generate.set_defaults(func=_generate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
