from pathlib import Path


def test_index_is_self_contained_and_has_favicon():
    """The static landing page should not depend on external assets at runtime."""
    html = Path("index.html").read_text(encoding="utf-8")

    assert 'rel="icon"' in html
    assert 'https://cdn.tailwindcss.com' not in html
    assert 'https://cdnjs.cloudflare.com' not in html
    assert 'tailwind.config' not in html
