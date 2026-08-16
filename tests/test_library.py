from bindery.library import append_entry, find_entry, load_index


def test_append_and_load(tmp_path):
    assert load_index(tmp_path) == []

    entry = append_entry(
        tmp_path, tmp_path / "deck.pptx", tmp_path / "deck.lock.json",
        "pptx", "reference@1.0.0", "2026-08-16T20:00:00Z",
    )
    entries = load_index(tmp_path)
    assert len(entries) == 1
    assert entries[0].id == entry.id
    assert entries[0].path == "deck.pptx"


def test_find_entry(tmp_path):
    entry = append_entry(
        tmp_path, tmp_path / "deck.pptx", tmp_path / "deck.lock.json",
        "pptx", "reference@1.0.0", "2026-08-16T20:00:00Z",
    )
    assert find_entry(tmp_path, entry.id) is not None
    assert find_entry(tmp_path, "nonexistent") is None
