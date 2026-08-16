import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DS = REPO_ROOT / "design-systems" / "reference"


@pytest.fixture
def ds_root(tmp_path):
    """A design-systems/ root containing a copy of the reference DS, so
    tests can mutate system.yaml / add overrides.json without touching the
    real fixture."""
    root = tmp_path / "design-systems"
    root.mkdir()
    shutil.copytree(REFERENCE_DS, root / "reference")
    return root
