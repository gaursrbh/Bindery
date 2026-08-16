import json

from bindery.cli import main


def _write_composition(path, *blocks):
    path.write_text(
        json.dumps(
            {
                "schema": "bindery/v1",
                "design_system": "reference@1.0.0",
                "target": "pptx",
                "blocks": list(blocks),
            }
        )
    )


def test_generate_success(ds_root, tmp_path, capsys):
    comp_path = tmp_path / "deck.json"
    _write_composition(
        comp_path, {"component": "title", "props": {"headline": "Q3 board update"}}
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = main(
        [
            "generate",
            str(comp_path),
            "--ds",
            "reference@1.0.0",
            "--out",
            str(out_dir),
            "--ds-root",
            str(ds_root),
        ]
    )

    assert code == 0
    out = capsys.readouterr().out.strip()
    assert out == str(out_dir / "deck.pptx")
    assert (out_dir / "deck.pptx").exists()


def test_generate_unresolvable_ds_exits_2(ds_root, tmp_path, capsys):
    comp_path = tmp_path / "deck.json"
    _write_composition(
        comp_path, {"component": "title", "props": {"headline": "Q3 board update"}}
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = main(
        [
            "generate",
            str(comp_path),
            "--ds",
            "reference@9.9.9",
            "--out",
            str(out_dir),
            "--ds-root",
            str(ds_root),
        ]
    )

    assert code == 2
    err = capsys.readouterr().err
    assert "version" in err


def test_generate_invalid_composition_exits_3(ds_root, tmp_path, capsys):
    comp_path = tmp_path / "deck.json"
    _write_composition(comp_path, {"component": "nonexistent", "props": {}})
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = main(
        [
            "generate",
            str(comp_path),
            "--ds",
            "reference@1.0.0",
            "--out",
            str(out_dir),
            "--ds-root",
            str(ds_root),
        ]
    )

    assert code == 3
    err = capsys.readouterr().err
    assert "available components" in err


def test_generate_overflow_exits_4(ds_root, tmp_path, capsys):
    comp_path = tmp_path / "deck.json"
    _write_composition(
        comp_path,
        {
            "component": "bullet-list",
            "props": {
                "heading": "This heading is long enough to wrap onto two lines of text",
                "items": [
                    "A" + " word" * 23,
                    "B" + " word" * 23,
                    "C" + " word" * 23,
                    "D" + " word" * 23,
                    "E" + " word" * 23,
                    "F" + " word" * 23,
                ],
            },
        },
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = main(
        [
            "generate",
            str(comp_path),
            "--ds",
            "reference@1.0.0",
            "--out",
            str(out_dir),
            "--ds-root",
            str(ds_root),
        ]
    )

    assert code == 4
    err = capsys.readouterr().err
    assert "block 0" in err
