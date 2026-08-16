"""Cross-shape geometric overlap checker — issue #41.

Catches the class of bug fixed reactively in issue #36 (blocks placed at
identical/overlapping coordinates) *before* an artifact ships, rather than
after a user reports "jumbled overlapped items." Checks pairwise bounding-box
overlap across blocks on the same slide — not within a single block's own
shapes, since a block may legitimately layer its own decorative elements
(e.g. editorial's accent-rule sitting directly against its headline text).
"""

from __future__ import annotations

from bindery.render.errors import RenderError


def _bbox(shape) -> tuple[int, int, int, int]:
    return (shape.left, shape.top, shape.left + shape.width, shape.top + shape.height)


def _overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    """Strict positive-area intersection — shapes that merely touch at an
    edge (share a boundary coordinate) are not considered overlapping."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2


def check_no_overlap(
    new_shapes: list, prior_shapes: list[tuple[object, int, str]], block_index: int, component: str
) -> None:
    """`prior_shapes` is a list of (shape, block_index, component) for every
    shape placed on the current slide by an *earlier* block. Raises
    RenderError naming both blocks on the first overlap found."""
    for ns in new_shapes:
        nb = _bbox(ns)
        for ps, prior_index, prior_component in prior_shapes:
            if _overlaps(nb, _bbox(ps)):
                raise RenderError(
                    block_index,
                    component,
                    f"shape overlaps block {prior_index} ({prior_component}) on the same slide",
                )
