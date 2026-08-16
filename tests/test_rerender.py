import json

import bindery.cli as cli


def _write_composition(path, target="pptx"):
    path.write_text(
        json.dumps(
            {
                "schema": "bindery/v1",
                "design_system": "reference@1.0.0",
                "target": target,
                "blocks": [{"component": "title", "props": {"headline": "Q3 board update"}}],
            }
        )
    )


def test_generate_then_rerender_byte_identical(ds_root, tmp_path):
    comp_path = tmp_path / "deck.json"
    _write_composition(comp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = cli.main(
        ["generate", str(comp_path), "--ds", "reference@1.0.0", "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    assert code == 0

    original_bytes = (out_dir / "deck.pptx").read_bytes()
    lock_path = out_dir / "deck.lock.json"
    assert lock_path.exists()

    rerender_dir = tmp_path / "rerender_out"
    rerender_dir.mkdir()
    code = cli.main(["rerender", str(lock_path), "--out", str(rerender_dir), "--ds-root", str(ds_root)])
    assert code == 0

    rerendered_bytes = (rerender_dir / "deck.pptx").read_bytes()
    assert rerendered_bytes == original_bytes


def test_rerender_by_library_id(ds_root, tmp_path):
    comp_path = tmp_path / "deck.json"
    _write_composition(comp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cli.main(
        ["generate", str(comp_path), "--ds", "reference@1.0.0", "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    entries = json.loads((out_dir / ".bindery-index.json").read_text())
    assert len(entries) == 1
    artifact_id = entries[0]["id"]

    code = cli.main(["rerender", artifact_id, "--out", str(out_dir), "--ds-root", str(ds_root)])
    assert code == 0


def test_rerender_fails_on_ds_change(ds_root, tmp_path):
    comp_path = tmp_path / "deck.json"
    _write_composition(comp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cli.main(
        ["generate", str(comp_path), "--ds", "reference@1.0.0", "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    lock_path = out_dir / "deck.lock.json"

    (ds_root / "reference" / "tokens.json").write_text(
        (ds_root / "reference" / "tokens.json").read_text() + " "
    )

    code = cli.main(["rerender", str(lock_path), "--out", str(out_dir), "--ds-root", str(ds_root)])
    assert code == 2
