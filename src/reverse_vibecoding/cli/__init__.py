"""CLI package exports."""

from typing import Any

__all__ = ["app", "run"]


def app(*args: Any, **kwargs: Any) -> Any:
    """Compatibility callable for older console scripts."""

    from reverse_vibecoding.cli.app import app as typer_app

    return typer_app(*args, **kwargs)


def run() -> None:
    """Console script entry point."""

    from reverse_vibecoding.cli.app import run as cli_run

    cli_run()
