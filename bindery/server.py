"""Local web UI backend — mainPRD §10 ("FastAPI, localhost only"), M4-spec.md §3.

Thin HTTP wrapper: every endpoint calls the same engine functions the CLI
calls (bindery.ds.loader, bindery.render, bindery.planner, bindery.lint,
bindery.lock, bindery.library) — no business logic lives here.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bindery import library
from bindery import lock as lock_module
from bindery.ds import loader
from bindery.ds.errors import DesignSystemError
from bindery.lint import lint as lint_dispatch
from bindery.planner.errors import PlannerError
from bindery.planner.ollama import OllamaPlanner, PlannerConfig
from bindery.planner.repair import plan_with_repair
from bindery.render import extension_for
from bindery.render import render as render_dispatch
from bindery.render.errors import CompositionError, RenderError, WebBuildError

_STATIC_DIR = Path(__file__).parent / "static"


class GenerateRequest(BaseModel):
    composition: dict
    ds: str


class PlanRequest(BaseModel):
    intent: str
    target: str
    design_system: str
    constraints: dict | None = None
    model: str | None = None


def _bind(ds, ds_spec: str, target: str, composition: dict, out_path: Path, models=None, seed=None):
    built = lock_module.build_lock(ds.path, ds_spec, target, composition, models=models, seed=seed)
    lock_path = out_path.with_suffix("").with_suffix(".lock.json")
    lock_module.write_lock(built, lock_path)
    return library.append_entry(out_path.parent, out_path, lock_path, target, ds_spec, built.created)


def create_app(out_dir: Path, ds_root: Path) -> FastAPI:
    out_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="Bindery")

    @app.get("/design-systems")
    def list_design_systems():
        return [
            {"name": ds.name, "version": ds.version, "targets": ds.targets}
            for ds in loader.list_installed(root=ds_root)
        ]

    @app.post("/generate")
    def generate(req: GenerateRequest):
        try:
            ds = loader.load(req.ds, root=ds_root)
        except DesignSystemError as e:
            raise HTTPException(422, str(e))

        target = req.composition.get("target")
        out_path = out_dir / f"artifact-{len(library.load_index(out_dir)) + 1}.{extension_for(target)}"
        try:
            result = render_dispatch(req.composition, ds, out_path)
        except (CompositionError, RenderError, WebBuildError) as e:
            raise HTTPException(422, str(e))

        entry = _bind(ds, ds.spec, target, req.composition, result.path)
        return asdict(entry)

    @app.post("/plan")
    def plan(req: PlanRequest):
        try:
            ds = loader.load(req.design_system, root=ds_root)
        except DesignSystemError as e:
            raise HTTPException(422, str(e))

        brief_text = req.intent
        if req.constraints:
            import yaml

            brief_text += f"\n\nConstraints:\n{yaml.safe_dump(req.constraints)}"

        config = PlannerConfig(model=req.model) if req.model else PlannerConfig()
        planner = OllamaPlanner(config)
        out_path = (
            out_dir / f"artifact-{len(library.load_index(out_dir)) + 1}.{extension_for(req.target)}"
        )

        try:
            result, composition = plan_with_repair(brief_text, ds, req.target, planner, out_path)
        except PlannerError as e:
            raise HTTPException(502, str(e))
        except (CompositionError, RenderError, WebBuildError) as e:
            raise HTTPException(422, str(e))

        entry = _bind(
            ds, ds.spec, req.target, composition, result.path,
            models={"planner": config.model}, seed=config.seed,
        )
        return asdict(entry)

    @app.get("/artifacts")
    def list_artifacts():
        return [asdict(e) for e in library.load_index(out_dir)]

    @app.get("/artifacts/{artifact_id}")
    def show_artifact(artifact_id: str):
        entry = library.find_entry(out_dir, artifact_id)
        if entry is None:
            raise HTTPException(404, f"no artifact with id {artifact_id!r}")
        built = lock_module.read_lock(out_dir / entry.lock_path)
        return {**asdict(entry), "lock": built.to_dict()}

    @app.get("/artifacts/{artifact_id}/file")
    def artifact_file(artifact_id: str):
        entry = library.find_entry(out_dir, artifact_id)
        if entry is None:
            raise HTTPException(404, f"no artifact with id {artifact_id!r}")
        return FileResponse(out_dir / entry.path)

    @app.post("/artifacts/{artifact_id}/rerender")
    def rerender_artifact(artifact_id: str):
        entry = library.find_entry(out_dir, artifact_id)
        if entry is None:
            raise HTTPException(404, f"no artifact with id {artifact_id!r}")

        built = lock_module.read_lock(out_dir / entry.lock_path)
        try:
            ds = loader.load(built.design_system, root=ds_root)
        except DesignSystemError as e:
            raise HTTPException(422, str(e))

        current_hash = lock_module.hash_design_system(ds.path)
        if current_hash != built.design_system_hash:
            raise HTTPException(
                409,
                f"design system '{built.design_system}' has changed since this lock was written",
            )

        try:
            result = render_dispatch(built.composition, ds, out_dir / entry.path)
        except (CompositionError, RenderError, WebBuildError) as e:
            raise HTTPException(422, str(e))
        return {"path": str(result.path)}

    @app.get("/lint")
    def lint_artifact(artifact: str, ds: str):
        artifact_path = Path(artifact)
        target = "pptx" if artifact_path.suffix == ".pptx" else "web"
        try:
            design_system = loader.load(ds, root=ds_root)
        except DesignSystemError as e:
            raise HTTPException(422, str(e))
        violations = lint_dispatch(artifact_path, design_system, target)
        return [{"location": v.location, "kind": v.kind, "value": v.value} for v in violations]

    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
    return app
