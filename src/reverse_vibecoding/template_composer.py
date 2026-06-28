"""Copy-tree template composition for generated projects."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateLayer:
    id: str
    source: Path


@dataclass(frozen=True)
class ComposeResult:
    target: Path
    applied_layers: tuple[str, ...]
    written_files: tuple[Path, ...]


def compose_template_layers(layers: list[TemplateLayer], target: Path) -> ComposeResult:
    """Copy template layers into `target` in order.

    The model is intentionally simple:

    - each layer is a complete directory tree fragment
    - files are copied relative to `target`
    - later layers overwrite earlier files at the same path
    - missing layer directories are rejected
    """

    target.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []

    for layer in layers:
        if not layer.source.exists():
            raise FileNotFoundError(f"Template layer does not exist: {layer.source}")
        if not layer.source.is_dir():
            raise NotADirectoryError(f"Template layer is not a directory: {layer.source}")

        for source_file in _iter_files(layer.source):
            relative_path = source_file.relative_to(layer.source)
            destination = target / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
            written_files.append(destination)

    return ComposeResult(
        target=target,
        applied_layers=tuple(layer.id for layer in layers),
        written_files=tuple(written_files),
    )


def _iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())

