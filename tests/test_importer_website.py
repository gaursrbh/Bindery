import io

from bindery.importer import candidate_tokens, scan_website, write_candidate_from_website

_FAKE_HTML = b"""
<html><head><style>
.hero { color: #1F3A5F; font-family: Georgia, serif; font-size: 40px; }
.button { background: #C97A2B; }
.noise1 { font-family: inherit; }
.noise2 { font-family: var(--_typography---font--display-serif-family); }
</style></head>
<body>
<div style="color:#1F3A5F;font-size:14px;">Text</div>
<div style="color:#1F3A5F;">More text</div>
</body></html>
"""


class _FakeHeaders:
    def get_content_charset(self):
        return "utf-8"


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body
        self.headers = _FakeHeaders()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_scan_website_extracts_colors_fonts_sizes(monkeypatch):
    def fake_urlopen(req, timeout):
        return _FakeResponse(_FAKE_HTML)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    report = scan_website("https://example.com")
    assert report.colors["#1F3A5F"] == 3
    assert report.colors["#C97A2B"] == 1
    assert report.fonts["Georgia"] == 1
    assert report.sizes[40] == 1
    assert report.sizes[14] == 1
    # Real regression: anthropic.com surfaced both of these as if they were
    # font names before the keyword/var() filter was added.
    assert "inherit" not in report.fonts
    assert not any(f.startswith("var(") for f in report.fonts)


def test_candidate_tokens_from_website_report(monkeypatch):
    def fake_urlopen(req, timeout):
        return _FakeResponse(_FAKE_HTML)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    report = scan_website("https://example.com")
    tokens = candidate_tokens(report)
    assert tokens["color"]["primary"]["value"] == "#1F3A5F"
    assert tokens["typography"]["family"]["value"] == "Georgia"


def test_write_candidate_from_website(monkeypatch, tmp_path):
    def fake_urlopen(req, timeout):
        return _FakeResponse(_FAKE_HTML)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    out_path = write_candidate_from_website("https://example.com", tmp_path)
    assert out_path.exists()
    import json
    data = json.loads(out_path.read_text())
    assert "color" in data and "typography" in data
