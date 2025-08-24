"""Minimal stub for python-dotenv when the real package isn't installed."""

def load_dotenv(*args, **kwargs) -> None:  # pragma: no cover - trivial
    """Stub implementation that does nothing."""
    return None

def find_dotenv(*args, **kwargs) -> str:  # pragma: no cover - trivial
    """Return empty string indicating no .env file found."""
    return ""

