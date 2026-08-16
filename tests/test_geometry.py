import pytest

from bindery.render.errors import RenderError
from bindery.render.geometry import _overlaps, check_no_overlap


class _FakeShape:
    def __init__(self, left, top, width, height):
        self.left, self.top, self.width, self.height = left, top, width, height
        self.has_text_frame = False


def test_overlaps_detects_intersection():
    a = (0, 0, 100, 100)
    b = (50, 50, 150, 150)
    assert _overlaps(a, b)


def test_overlaps_false_for_adjacent_touching_edges():
    a = (0, 0, 100, 100)
    b = (100, 0, 200, 100)  # shares the x=100 boundary, no area overlap
    assert not _overlaps(a, b)


def test_overlaps_false_for_disjoint():
    a = (0, 0, 10, 10)
    b = (100, 100, 110, 110)
    assert not _overlaps(a, b)


def test_check_no_overlap_raises_on_real_overlap():
    prior = [(_FakeShape(0, 0, 100, 100), 0, "title")]
    new = [_FakeShape(50, 50, 100, 100)]
    with pytest.raises(RenderError, match="overlaps block 0"):
        check_no_overlap(new, prior, 1, "stat-trio")


def test_check_no_overlap_passes_for_legal_adjacent_shapes():
    prior = [(_FakeShape(0, 0, 100, 100), 0, "title")]
    new = [_FakeShape(0, 100, 100, 100)]  # directly below, no overlap
    check_no_overlap(new, prior, 1, "stat-trio")  # should not raise
