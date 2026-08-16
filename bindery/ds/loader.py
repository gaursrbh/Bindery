"""Design System loader — mainPRD R2, M0-spec.md §3."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from bindery.ds.errors import DesignSystemError

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_SPEC_RE = re.compile(r"^([a-z0-9_-]+)(?:@(.+))?$")

SCHEMA_ROOT = Path(__file__).resolve().parent.parent.parent / "schema"

# Component name -> base target vocab schema file, per target.
_TARGET_VOCAB_FILES = {
    "pptx": "pptx.schema.json",
    "web": "web.schema.json",
    "infographic": "infographic.schema.json",
    "html-slides": "html-slides.schema.json",
}

# Targets whose components are Python layout functions, loaded via
# importlib by _load_layout_fns. Non-Python targets (e.g. "web", M2-spec.md
# §2 — .jsx modules built by a per-DS Vite pipeline) manage their own
# component loading inside their renderer, not through DesignSystem.layout_fns.
# "infographic" (M4-spec.md §2.2) uses Python components too, different
# signature (layout(props, tokens, x, y, width) -> str) but the loader
# doesn't care — it just imports the module and stores `layout`.
_PYTHON_LAYOUT_TARGETS = {"pptx", "infographic", "html-slides"}


def _parse_semver(version: str, file: str, field_name: str) -> tuple[int, int, int]:
    m = _SEMVER_RE.match(version)
    if not m:
        raise DesignSystemError(
            file, field_name, f'"{version}" is not valid semver'
        )
    return tuple(int(g) for g in m.groups())  # type: ignore[return-value]


@dataclass
class ValidationIssue:
    message: str


@dataclass
class DesignSystem:
    name: str
    version: str
    tokens: dict
    targets: list[str]
    effective_schemas: dict[str, dict] = field(default_factory=dict)
    layout_fns: dict[str, dict[str, Callable]] = field(default_factory=dict)
    component_docs: dict[str, dict[str, str]] = field(default_factory=dict)
    path: Path = None  # type: ignore[assignment]

    @property
    def spec(self) -> str:
        return f"{self.name}@{self.version}"


def _load_base_schema_store() -> dict[str, dict]:
    """Return {$id/filename: schema} for core + target vocabs, so $ref
    resolution between them works regardless of target."""
    store = {}
    for fname in ["core.schema.json", *_TARGET_VOCAB_FILES.values()]:
        p = SCHEMA_ROOT / fname
        with open(p) as f:
            store[fname] = json.load(f)
    return store


def _read_system_yaml(ds_dir: Path) -> dict:
    sy_path = ds_dir / "system.yaml"
    if not sy_path.exists():
        raise DesignSystemError("system.yaml", "<file>", "not found")
    try:
        with open(sy_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise DesignSystemError("system.yaml", "<file>", f"invalid YAML: {e}")

    if not isinstance(data, dict):
        raise DesignSystemError("system.yaml", "<file>", "must be a mapping")

    for required in ("name", "version", "description", "targets"):
        if required not in data:
            raise DesignSystemError("system.yaml", required, "missing")

    _parse_semver(str(data["version"]), "system.yaml", "version")

    if not isinstance(data["targets"], list) or not data["targets"]:
        raise DesignSystemError("system.yaml", "targets", "must be a non-empty list")

    return data


def _merge_overrides(base_vocab: dict, overrides: dict | None, target: str) -> dict:
    """Additive-only merge per M0-spec.md §2.4: DS may add components (extra
    oneOf branches) and extra optional props on existing components; may not
    remove required props or widen an existing enum."""
    if not overrides or target not in overrides:
        return base_vocab

    merged = copy.deepcopy(base_vocab)
    target_overrides = overrides[target]

    defs = merged.setdefault("$defs", {})
    oneof_items = merged["allOf"][1]["properties"]["blocks"]["items"]["oneOf"]

    for comp_name, comp_spec in target_overrides.get("components", {}).items():
        def_key = comp_name.replace("-", "_") + "_override"
        defs[def_key] = {
            "type": "object",
            "additionalProperties": False,
            "required": ["component", "props"],
            "properties": {
                "component": {"const": comp_name},
                "props": comp_spec["props"],
            },
        }
        oneof_items.append({"$ref": f"#/$defs/{def_key}"})

    for comp_name, extra in target_overrides.get("extend_props", {}).items():
        if comp_name not in defs:
            continue
        props_schema = defs[comp_name]["properties"]["props"]
        for prop_name, prop_schema in extra.get("optional", {}).items():
            props_schema.setdefault("properties", {})[prop_name] = prop_schema

    return merged


def _load_component_docs(ds_dir: Path, targets: list[str]) -> dict[str, dict[str, str]]:
    """M1-spec.md §2.3: optional `description` field on overrides.json
    components/extend_props entries -> DesignSystem.component_docs, kept
    DS-agnostic (base-component docs live in bindery/planner/, not here)."""
    overrides_path = ds_dir / "schema" / "overrides.json"
    if not overrides_path.exists():
        return {}
    with open(overrides_path) as f:
        overrides = json.load(f)

    docs: dict[str, dict[str, str]] = {}
    for target in targets:
        target_overrides = overrides.get(target)
        if not target_overrides:
            continue
        target_docs: dict[str, str] = {}
        for comp_name, comp_spec in target_overrides.get("components", {}).items():
            if "description" in comp_spec:
                target_docs[comp_name] = comp_spec["description"]
        for comp_name, extra in target_overrides.get("extend_props", {}).items():
            for prop_name, prop_schema in extra.get("optional", {}).items():
                if "description" in prop_schema:
                    target_docs[f"{comp_name}.{prop_name}"] = prop_schema["description"]
        if target_docs:
            docs[target] = target_docs
    return docs


def _load_effective_schemas(ds_dir: Path, targets: list[str]) -> dict[str, dict]:
    store = _load_base_schema_store()

    overrides = None
    overrides_path = ds_dir / "schema" / "overrides.json"
    if overrides_path.exists():
        with open(overrides_path) as f:
            overrides = json.load(f)

    effective = {}
    for target in targets:
        vocab_file = _TARGET_VOCAB_FILES.get(target)
        if vocab_file is None:
            continue
        base_vocab = store[vocab_file]
        effective[target] = _merge_overrides(base_vocab, overrides, target)
    return effective


def _load_layout_fns(ds_dir: Path, effective_schemas: dict[str, dict]) -> dict[str, dict[str, Callable]]:
    layout_fns: dict[str, dict[str, Callable]] = {}

    for target, schema in effective_schemas.items():
        if target not in _PYTHON_LAYOUT_TARGETS:
            continue
        target_fns: dict[str, Callable] = {}
        components_dir = ds_dir / "components" / target
        component_names = _component_names(schema)

        for comp_name in component_names:
            module_name = comp_name  # e.g. "stat-trio"
            module_path = components_dir / f"{module_name}.py"
            if not module_path.exists():
                raise DesignSystemError(
                    str(module_path.relative_to(ds_dir)),
                    "layout",
                    f"missing layout module for component '{comp_name}'",
                )
            spec = importlib.util.spec_from_file_location(
                f"bindery_ds_{ds_dir.name}_{target}_{module_name.replace('-', '_')}",
                module_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            if not hasattr(module, "layout"):
                raise DesignSystemError(
                    str(module_path.relative_to(ds_dir)),
                    "layout",
                    "module does not define a `layout` function",
                )
            target_fns[comp_name] = module.layout

        layout_fns[target] = target_fns

    return layout_fns


def _component_names(effective_schema: dict) -> list[str]:
    defs = effective_schema.get("$defs", {})
    names = []
    for def_schema in defs.values():
        const = def_schema.get("properties", {}).get("component", {}).get("const")
        if const:
            names.append(const)
    return names


def _resolve_version(name: str, version_spec: str | None, root: Path) -> Path:
    candidates = [p for p in root.iterdir() if p.is_dir() and p.name.startswith(f"{name}")]
    # DS directories are named by DS name only; versions live inside system.yaml.
    # For M0, one directory per DS name (single installed version per name is the
    # common case); support multiple by scanning subdirectories named <name>-<version>
    # is out of scope for M0 — resolve within the single `root/<name>` directory.
    ds_dir = root / name
    if not ds_dir.is_dir():
        raise DesignSystemError(name, "<design-system>", f"not installed under {root}")

    installed = _read_system_yaml(ds_dir)
    installed_version = installed["version"]

    if version_spec is None:
        return ds_dir

    if version_spec.endswith(".x") or re.match(r"^\d+$", version_spec):
        prefix = version_spec[:-2] if version_spec.endswith(".x") else version_spec
        if not installed_version.startswith(prefix + "."):
            raise DesignSystemError(
                name, "version", f"no installed version matches '{version_spec}'"
            )
        return ds_dir

    _parse_semver(version_spec, "<cli>", "--ds")
    if installed_version != version_spec:
        raise DesignSystemError(
            name, "version", f"'{version_spec}' is not installed (have {installed_version})"
        )
    return ds_dir


def load(name_or_spec: str, root: Path = Path("design-systems")) -> DesignSystem:
    m = _SPEC_RE.match(name_or_spec)
    if not m:
        raise DesignSystemError(name_or_spec, "<spec>", "malformed design-system spec")
    name, version_spec = m.group(1), m.group(2)

    ds_dir = _resolve_version(name, version_spec, root)
    system = _read_system_yaml(ds_dir)

    tokens_path = ds_dir / "tokens.json"
    if not tokens_path.exists():
        raise DesignSystemError("tokens.json", "<file>", "not found")
    try:
        with open(tokens_path) as f:
            tokens = json.load(f)
    except json.JSONDecodeError as e:
        raise DesignSystemError("tokens.json", "<file>", f"invalid JSON: {e}")

    effective_schemas = _load_effective_schemas(ds_dir, system["targets"])
    layout_fns = _load_layout_fns(ds_dir, effective_schemas)
    component_docs = _load_component_docs(ds_dir, system["targets"])

    return DesignSystem(
        name=system["name"],
        version=str(system["version"]),
        tokens=tokens,
        targets=system["targets"],
        effective_schemas=effective_schemas,
        layout_fns=layout_fns,
        component_docs=component_docs,
        path=ds_dir,
    )


def list_installed(root: Path = Path("design-systems")) -> list[DesignSystem]:
    if not root.is_dir():
        return []
    result = []
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / "system.yaml").exists():
            result.append(load(entry.name, root=root))
    return result


def validate(ds: DesignSystem) -> list[ValidationIssue]:
    """Structural check only — system.yaml/tokens.json already parsed by
    load(); this re-confirms every effective-schema component has a matching
    layout function (load() would have raised already, so this mainly exists
    as a non-raising check for tooling/CLI `bindery ds validate`)."""
    issues: list[ValidationIssue] = []
    for target, schema in ds.effective_schemas.items():
        if target not in _PYTHON_LAYOUT_TARGETS:
            continue  # non-Python targets (e.g. web) manage their own component loading
        fns = ds.layout_fns.get(target, {})
        for comp_name in _component_names(schema):
            if comp_name not in fns:
                issues.append(
                    ValidationIssue(
                        f"{target}: component '{comp_name}' has no layout function"
                    )
                )
    return issues
