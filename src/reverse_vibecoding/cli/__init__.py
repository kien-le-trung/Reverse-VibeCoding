"""CLI package exports."""

from typing import Any

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    if name == "app":
        from reverse_vibecoding.cli.app import app

        return app
    raise AttributeError(name)
