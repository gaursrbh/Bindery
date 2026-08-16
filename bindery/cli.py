"""CLI — mainPRD R10, M0-spec.md §5."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from bindery import library, lock as lock_module
from bindery.ds import loader
from bindery.ds.errors import DesignSystemError
from bindery.lint import lint as lint_dispatch
from bindery.planner.claude_cli import ClaudeCliConfig, ClaudeCliPlanner
from bindery.planner.errors import PlannerError
from bindery.planner.ollama import OllamaPlanner, PlannerConfig
from bindery.planner.repair import plan_with_repair
from bindery.render import extension_for
from bindery.render import render as render_dispatch
from bindery.render.errors import CompositionError, RenderError, WebBuildError


def _bind(ds, ds_spec: str, target: str, composition: dict, out_path: Path, models=None, seed=None):
    """mainPRD §7 step 7 — write bindery.lock, then append the artifact
    library index entry (M3-spec.md §3.3, §4.3)."""
    built = lock_module.build_lock(ds.path, ds_spec, target, composition, models=models, seed=seed)
    lock_path = out_path.with_suffix("").with_suffix(".lock.json")
    lock_module.write_lock(built, lock_path)
    library.append_entry(out_path.parent, out_path, lock_path, target, ds_spec, built.created)


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

    _bind(ds, ds.spec, composition["target"], composition, result.path)
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

    if args.planner == "claude-cli":
        cli_config = ClaudeCliConfig(model=args.model) if args.model else ClaudeCliConfig()
        planner = ClaudeCliPlanner(cli_config)
        model_name, seed = cli_config.model, None
    else:
        config = PlannerConfig(model=args.model) if args.model else PlannerConfig()
        planner = OllamaPlanner(config)
        model_name, seed = config.model, config.seed

    out_path = Path(args.out) / f"{brief_path.stem}.{extension_for(target)}"

    try:
        result, composition = plan_with_repair(brief_text, ds, target, planner, out_path)
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

    _bind(
        ds, ds.spec, target, composition, result.path,
        models={"planner": model_name}, seed=seed,
    )
    print(str(result.path))
    return 0


def _lint(args: argparse.Namespace) -> int:
    artifact_path = Path(args.artifact)
    if args.target:
        target = args.target
    elif artifact_path.suffix == ".pptx":
        target = "pptx"
    else:
        target = "web"  # ambiguous with html-slides (.html) — override with --target

    try:
        ds = loader.load(args.ds, root=Path(args.ds_root))
    except DesignSystemError as e:
        print(str(e), file=sys.stderr)
        return 2

    violations = lint_dispatch(artifact_path, ds, target)
    for v in violations:
        print(f"{v.location}: off-token {v.kind} {v.value!r}", file=sys.stderr)

    if violations:
        return 7
    print("0 violations")
    return 0


def _rerender(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    lock_path = Path(args.target_)
    if not lock_path.exists():
        entry = library.find_entry(out_dir, args.target_)
        if entry is None:
            print(f"no artifact with id {args.target_!r} in {out_dir}", file=sys.stderr)
            return 2
        lock_path = out_dir / entry.lock_path

    built = lock_module.read_lock(lock_path)

    try:
        ds = loader.load(built.design_system, root=Path(args.ds_root))
    except DesignSystemError as e:
        print(str(e), file=sys.stderr)
        return 2

    current_hash = lock_module.hash_design_system(ds.path)
    if current_hash != built.design_system_hash:
        print(
            f"design system '{built.design_system}' has changed since this lock was "
            f"written (lock: {built.design_system_hash}, current: {current_hash})",
            file=sys.stderr,
        )
        return 2

    ext = extension_for(built.composition["target"])
    out_path = out_dir / f"{lock_path.stem.removesuffix('.lock')}.{ext}"

    try:
        result = render_dispatch(built.composition, ds, out_path)
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


def _list(args: argparse.Namespace) -> int:
    for e in library.load_index(Path(args.out)):
        print(f"{e.id}  {e.target:5s}  {e.design_system:20s}  {e.created}  {e.path}")
    return 0


def _show(args: argparse.Namespace) -> int:
    entry = library.find_entry(Path(args.out), args.id)
    if entry is None:
        print(f"no artifact with id {args.id!r}", file=sys.stderr)
        return 2
    for k, v in entry.__dict__.items():
        print(f"{k}: {v}")
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    from bindery.server import create_app

    app = create_app(Path(args.out), Path(args.ds_root))
    uvicorn.run(app, host="127.0.0.1", port=args.port)
    return 0


def _import(args: argparse.Namespace) -> int:
    from bindery.importer import scan_pptx, write_candidate

    deck_path = Path(args.deck)
    report = scan_pptx(deck_path)
    print(f"colors seen: {dict(report.colors.most_common())}", file=sys.stderr)
    print(f"sizes seen: {dict(report.sizes.most_common())}", file=sys.stderr)
    print(f"fonts seen: {dict(report.fonts.most_common())}", file=sys.stderr)

    out_path = write_candidate(deck_path, Path(args.out))
    print(str(out_path))
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
    plan.add_argument("--planner", choices=["ollama", "claude-cli"], default="ollama")
    plan.add_argument("--out", required=True)
    plan.add_argument("--ds-root", default="design-systems")
    plan.set_defaults(func=_plan)

    lint = subparsers.add_parser("lint", help="Check a rendered artifact for off-token values")
    lint.add_argument("artifact")
    lint.add_argument("--ds", required=True)
    lint.add_argument("--ds-root", default="design-systems")
    lint.add_argument("--target", default=None, help="Override target detection (needed for .html — ambiguous between web/html-slides)")
    lint.set_defaults(func=_lint)

    rerender = subparsers.add_parser(
        "rerender", help="Re-render an artifact from its lock file or library id"
    )
    rerender.add_argument("target_", metavar="lock-or-id")
    rerender.add_argument("--out", required=True)
    rerender.add_argument("--ds-root", default="design-systems")
    rerender.set_defaults(func=_rerender)

    list_cmd = subparsers.add_parser("list", help="List artifacts in the library index")
    list_cmd.add_argument("--out", required=True)
    list_cmd.set_defaults(func=_list)

    show = subparsers.add_parser("show", help="Show one artifact's library entry")
    show.add_argument("id")
    show.add_argument("--out", required=True)
    show.set_defaults(func=_show)

    serve = subparsers.add_parser("serve", help="Run the local web UI (FastAPI, localhost only)")
    serve.add_argument("--port", type=int, default=8420)
    serve.add_argument("--out", required=True)
    serve.add_argument("--ds-root", default="design-systems")
    serve.set_defaults(func=_serve)

    import_cmd = subparsers.add_parser(
        "import", help="Extract a candidate tokens.json from an existing .pptx deck"
    )
    import_cmd.add_argument("deck")
    import_cmd.add_argument("--out", required=True)
    import_cmd.set_defaults(func=_import)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
