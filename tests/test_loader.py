import pytest

from bindery.ds import loader
from bindery.ds.errors import DesignSystemError


def test_load_reference_ds(ds_root):
    ds = loader.load("reference", root=ds_root)
    assert ds.name == "reference"
    assert ds.version == "1.0.0"
    assert ds.targets == ["pptx", "web", "infographic"]
    assert set(ds.layout_fns["pptx"]) == {
        "title",
        "stat-trio",
        "bullet-list",
        "image-callout",
    }
    assert loader.validate(ds) == []


def test_load_exact_version(ds_root):
    ds = loader.load("reference@1.0.0", root=ds_root)
    assert ds.spec == "reference@1.0.0"


def test_load_version_range(ds_root):
    ds = loader.load("reference@1.x", root=ds_root)
    assert ds.spec == "reference@1.0.0"


def test_load_unresolvable_exact_version(ds_root):
    with pytest.raises(DesignSystemError) as exc:
        loader.load("reference@9.9.9", root=ds_root)
    assert "version" in str(exc.value)


def test_load_unresolvable_version_range(ds_root):
    with pytest.raises(DesignSystemError):
        loader.load("reference@9.x", root=ds_root)


def test_load_not_installed(ds_root):
    with pytest.raises(DesignSystemError):
        loader.load("nonexistent", root=ds_root)


def test_malformed_system_yaml_missing_field(ds_root):
    sy = ds_root / "reference" / "system.yaml"
    sy.write_text("name: reference\nversion: 1.0.0\n")  # missing description, targets
    with pytest.raises(DesignSystemError) as exc:
        loader.load("reference", root=ds_root)
    assert exc.value.field == "description"


def test_malformed_system_yaml_bad_semver(ds_root):
    sy = ds_root / "reference" / "system.yaml"
    sy.write_text(
        "name: reference\nversion: 1.x\ndescription: d\ntargets: [pptx]\n"
    )
    with pytest.raises(DesignSystemError) as exc:
        loader.load("reference", root=ds_root)
    assert exc.value.field == "version"
    assert "not valid semver" in str(exc.value)


def test_missing_tokens_json(ds_root):
    (ds_root / "reference" / "tokens.json").unlink()
    with pytest.raises(DesignSystemError) as exc:
        loader.load("reference", root=ds_root)
    assert exc.value.file == "tokens.json"


def test_missing_layout_module_fails_fast(ds_root):
    (ds_root / "reference" / "components" / "pptx" / "title.py").unlink()
    with pytest.raises(DesignSystemError) as exc:
        loader.load("reference", root=ds_root)
    assert "title" in exc.value.detail


def test_list_installed(ds_root):
    installed = loader.list_installed(root=ds_root)
    assert [ds.name for ds in installed] == ["reference"]
