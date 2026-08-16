class CompositionError(Exception):
    """Raised when a composition fails validation against a DS's effective
    schema. Message lists available components (mainPRD R3)."""

    def __init__(self, message: str):
        super().__init__(message)


class RenderError(Exception):
    """Raised when a placed block cannot be rendered as specified — e.g. text
    overflowing its frame (mainPRD R4). Names the offending block index and
    prop, never silently clips."""

    def __init__(self, block_index: int, prop: str, detail: str):
        self.block_index = block_index
        self.prop = prop
        self.detail = detail
        super().__init__(f"block {block_index} ({prop}): {detail}")


class WebBuildError(Exception):
    """Raised when the per-DS Vite build subprocess exits non-zero
    (M2-spec.md §2.4) — the web renderer's deterministic-failure analogue to
    PPTX's overflow check, since a page reflows rather than overflowing."""

    def __init__(self, stderr: str):
        self.stderr = stderr
        super().__init__(f"web build failed: {stderr}")
