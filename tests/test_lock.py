from bindery.lock import build_lock, hash_design_system, read_lock, write_lock


def test_hash_stable_and_sensitive_to_content(ds_root):
    ds_path = ds_root / "reference"
    h1 = hash_design_system(ds_path)
    h2 = hash_design_system(ds_path)
    assert h1 == h2
    assert h1.startswith("sha256:")

    (ds_path / "tokens.json").write_text((ds_path / "tokens.json").read_text() + " ")
    h3 = hash_design_system(ds_path)
    assert h3 != h1


def test_hash_ignores_generated_web_files(ds_root):
    ds_path = ds_root / "reference"
    h1 = hash_design_system(ds_path)
    web_src = ds_path / "components" / "web" / "src"
    web_src.mkdir(parents=True, exist_ok=True)
    (web_src / "tokens.css").write_text(":root{--x:1;}")
    (web_src / ".bindery-entry.jsx").write_text("// generated")
    h2 = hash_design_system(ds_path)
    assert h1 == h2


def test_lock_round_trip(ds_root, tmp_path):
    ds_path = ds_root / "reference"
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0",
        "target": "pptx", "blocks": [{"component": "title", "props": {"headline": "x"}}],
    }
    built = build_lock(ds_path, "reference@1.0.0", "pptx", composition, models={"planner": "m"}, seed=42)
    path = tmp_path / "deck.lock.json"
    write_lock(built, path)

    read_back = read_lock(path)
    assert read_back.design_system == "reference@1.0.0"
    assert read_back.design_system_hash == built.design_system_hash
    assert read_back.composition == composition
    assert read_back.seed == 42
    assert read_back.models == {"planner": "m"}
