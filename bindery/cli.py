"""CLI — mainPRD R10, M0-spec.md §5."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from bindery.ds import loader
from bindery.ds.errors import DesignSystemError
from bindery.planner.errors import PlannerError
from bindery.planner.ollama import OllamaPlanner, PlannerConfig
from bindery.planner.repair import plan_with_repair
from bindery.render import extension_for
from bindery.render import render as render_dispatch
from bindery.render.errors import CompositionError, RenderError, WebBuildError


def _generate(args: argparse.Namespace) -> int:
    composition_path = Path(args.composition)
    composition = json.loads(composition_path.read_text())

    try:
        ds = loader.load(args.ds, root=Path(args.ds_root))
    except DesignSystemError as e:
        print(str(e), file=sys.stderr)
        return 2

    out_path = Path(args.out) / f"{composition_path.stem}.{extension_for(composition.get('target'))}"

    try:
        result = render_dispatch(composition, ds, out_path)
    except CompositionError as e:
        print(str(e), file=sys.stderr)
        return 3
    except RenderError as e:
        print(str(e), file=sys.stderr)
        return 4
    except WebBuildError as e:
        print(str(e), file=sys.stderr)
        return 6

    print(str(result.path))
    return 0


def _plan(args: argparse.Namespace) -> int:
    brief_path = Path(args.brief)
    brief_doc = yaml.safe_load(brief_path.read_text())

    ds_spec = args.ds or brief_doc.get("design_system")
    target = args.target or brief_doc.get("target")
    if not ds_spec:
        print("no design system: pass --ds or set design_system in the brief", file=sys.stderr)
        return 2
    if not target:
        print("no target: pass --target or set target in the brief", file=sys.stderr)
        return 2

    try:
        ds = loader.load(ds_spec, root=Path(args.ds_root))
    except DesignSystemError as e:
        print(str(e), file=sys.stderr)
        return 2

    intent = brief_doc.get("intent", "")
    constraints = brief_doc.get("constraints", {})
    brief_text = intent
    if constraints:
        brief_text += f"\n\nConstraints:\n{yaml.safe_dump(constraints)}"

    config = PlannerConfig(model=args.model) if args.model else PlannerConfig()
    planner = OllamaPlanner(config)

    out_path = Path(args.out) / f"{brief_path.stem}.{extension_for(target)}"

    try:
        result = plan_with_repair(brief_text, ds, target, planner, out_path)
    except PlannerError as e:
        print(str(e), file=sys.stderr)
        return 5
    except CompositionError as e:
        print(str(e), file=sys.stderr)
        return 3
    except RenderError as e:
        print(str(e), file=sys.stderr)
        return 4
    except WebBuildError as e:
        print(str(e), file=sys.stderr)
        return 6

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

    plan = subparsers.add_parser(
        "plan", help="Plan a brief with a local model and render it to a .pptx"
    )
    plan.add_argument("brief")
    plan.add_argument("--ds", default=None)
    plan.add_argument("--target", default=None)
    plan.add_argument("--model", default=None)
    plan.add_argument("--out", required=True)
    plan.add_argument("--ds-root", default="design-systems")
    plan.set_defaults(func=_plan)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
