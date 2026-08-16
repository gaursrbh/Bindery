import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DS = REPO_ROOT / "design-systems" / "reference"


@pytest.fixture
def ds_root(tmp_path):
    """A design-systems/ root containing a copy of the reference DS, so
    tests can mutate system.yaml / add overrides.json without touching the
    real fixture. Excludes components/web/node_modules — real, ~70-package
    npm install, too slow to deep-copy per test; see `ds_root_with_web` for
    tests that need it."""
    root = tmp_path / "design-systems"
    root.mkdir()
    shutil.copytree(
        REFERENCE_DS, root / "reference", ignore=shutil.ignore_patterns("node_modules")
    )
    return root


@pytest.fixture
def ds_root_with_web(ds_root):
    """Same as ds_root, but with components/web/node_modules symlinked in
    from the real fixture (not copied) for tests that actually invoke
    `npm run build` (tests/test_render_web.py)."""
    real_node_modules = REFERENCE_DS / "components" / "web" / "node_modules"
    if real_node_modules.is_dir():
        (ds_root / "reference" / "components" / "web" / "node_modules").symlink_to(
            real_node_modules
        )
    return ds_root
