"""Resolve template manifests into ordered copy-tree layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reverse_vibecoding.template_composer import TemplateLayer


LEVEL_ORDER: dict[str, tuple[str, ...]] = {
    "fastapi": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "nodejs": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "flask": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "django": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "spring_boot": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "react_native": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "vue": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "react": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
    "angular": (
        "level_1",
        "level_2",
        "level_3",
        "level_4",
    ),
}

BASE_BY_STACK: dict[str, str] = {
    "fastapi": "fastapi_base",
    "nodejs": "nodejs_base",
    "flask": "flask_base",
    "django": "django_base",
    "spring_boot": "spring_boot_base",
    "react_native": "react_native_base",
    "vue": "vue_base",
    "react": "react_base",
    "angular": "angular_base",
}


@dataclass(frozen=True)
class TemplateSelection:
    stack: str
    level: str
    domains: tuple[str, ...] = ()
    databases: tuple[str, ...] = ()
    scenarios: tuple[str, ...] = ()
    bug_seeds: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedTemplate:
    layers: tuple[TemplateLayer, ...]
    manifest_ids: tuple[str, ...]
    checks: tuple[str, ...] = ()
    python_dependencies: tuple[str, ...] = ()
    npm_dependencies: tuple[str, ...] = ()
    npm_dev_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class OverlayManifest:
    id: str
    type: str
    path: Path
    data: dict[str, Any]
    stacks: tuple[str, ...] = ()
    requires: dict[str, str] = field(default_factory=dict)
    conflicts: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    python_dependencies: tuple[str, ...] = ()
    npm_dependencies: tuple[str, ...] = ()
    npm_dev_dependencies: tuple[str, ...] = ()

    @property
    def files_dir(self) -> Path:
        return self.path.parent / "files"


def resolve_template_layers(templates_root: Path, selection: TemplateSelection) -> ResolvedTemplate:
    """Resolve a stack selection into ordered copy-tree layers.

    The resolver expands a requested level into the cumulative level chain. For example,
    FastAPI level 4 resolves to base, level 1, level 2, level 3, and level 4, followed by
    selected domain/database/scenario/bug overlays.
    """

    manifests = _load_manifests(templates_root)
    selected = _resolve_stack_and_levels(templates_root, manifests, selection.stack, selection.level)

    for group, overlay_type in (
        (selection.domains, "domain"),
        (selection.databases, "database"),
        (selection.scenarios, "scenario"),
        (selection.bug_seeds, "bug_seed"),
    ):
        for overlay_id in group:
            manifest = _require_manifest(manifests, overlay_id, stack=selection.stack, overlay_type=overlay_type)
            if manifest.type != overlay_type:
                raise ValueError(f"Overlay {overlay_id!r} is type {manifest.type!r}, not {overlay_type!r}")
            selected.append(manifest)

    _validate_selection(selected, selection.stack, selection.level)

    layers = tuple(
        TemplateLayer(manifest.id, manifest.files_dir)
        for manifest in selected
        if manifest.files_dir.exists()
    )
    checks = tuple(check for manifest in selected for check in manifest.checks)
    python_dependencies = tuple(
        dict.fromkeys(dependency for manifest in selected for dependency in manifest.python_dependencies)
    )
    npm_dependencies = tuple(
        dict.fromkeys(dependency for manifest in selected for dependency in manifest.npm_dependencies)
    )
    npm_dev_dependencies = tuple(
        dict.fromkeys(dependency for manifest in selected for dependency in manifest.npm_dev_dependencies)
    )

    return ResolvedTemplate(
        layers=layers,
        manifest_ids=tuple(manifest.id for manifest in selected),
        checks=checks,
        python_dependencies=python_dependencies,
        npm_dependencies=npm_dependencies,
        npm_dev_dependencies=npm_dev_dependencies,
    )


def _resolve_stack_and_levels(
    templates_root: Path,
    manifests: dict[str, list[OverlayManifest]],
    stack: str,
    target_level: str,
) -> list[OverlayManifest]:
    if stack not in LEVEL_ORDER:
        raise ValueError(f"Unsupported stack: {stack}")
    if target_level not in LEVEL_ORDER[stack]:
        raise ValueError(f"Unsupported level {target_level!r} for stack {stack!r}")

    base_id = BASE_BY_STACK[stack]
    selected = [_require_manifest(manifests, base_id, stack=stack, overlay_type="stack_base")]

    level_ids = LEVEL_ORDER[stack]
    target_index = level_ids.index(target_level)
    selected.extend(
        _require_manifest(manifests, level_id, stack=stack, overlay_type="completeness_level")
        for level_id in level_ids[: target_index + 1]
    )
    return selected


def _validate_selection(manifests: list[OverlayManifest], stack: str, target_level: str) -> None:
    ids = tuple(manifest.id for manifest in manifests)
    id_set = set(ids)

    for manifest in manifests:
        if manifest.stacks and stack not in manifest.stacks:
            raise ValueError(f"Overlay {manifest.id!r} does not support stack {stack!r}")

        min_level = manifest.requires.get("min_level")
        if min_level and _level_index(stack, target_level) < _level_index(stack, min_level):
            raise ValueError(
                f"Overlay {manifest.id!r} requires at least {min_level!r}, got {target_level!r}"
            )

        required_base = manifest.requires.get("base")
        if required_base and required_base not in id_set:
            raise ValueError(f"Overlay {manifest.id!r} requires base {required_base!r}")

        conflicts = id_set.intersection(manifest.conflicts)
        if conflicts:
            conflict_list = ", ".join(sorted(conflicts))
            raise ValueError(f"Overlay {manifest.id!r} conflicts with: {conflict_list}")


def _level_index(stack: str, level: str) -> int:
    try:
        return LEVEL_ORDER[stack].index(level)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unknown level {level!r} for stack {stack!r}") from exc


def _load_manifests(templates_root: Path) -> dict[str, list[OverlayManifest]]:
    manifests: dict[str, list[OverlayManifest]] = {}
    for path in sorted(templates_root.rglob("overlay.yaml")):
        manifest = _parse_manifest(path)
        manifests.setdefault(manifest.id, []).append(manifest)
    return manifests


def _require_manifest(
    manifests: dict[str, list[OverlayManifest]],
    overlay_id: str,
    *,
    stack: str,
    overlay_type: str,
) -> OverlayManifest:
    try:
        candidates = manifests[overlay_id]
    except KeyError as exc:
        raise ValueError(f"Unknown overlay id: {overlay_id}") from exc

    matches = [
        manifest
        for manifest in candidates
        if manifest.type == overlay_type and (not manifest.stacks or stack in manifest.stacks)
    ]
    if not matches:
        raise ValueError(f"Overlay {overlay_id!r} does not match stack {stack!r} and type {overlay_type!r}")
    if len(matches) > 1:
        paths = ", ".join(str(manifest.path) for manifest in matches)
        raise ValueError(f"Ambiguous overlay {overlay_id!r} for stack {stack!r}: {paths}")
    return matches[0]


def _parse_manifest(path: Path) -> OverlayManifest:
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    manifest_id = str(data["id"])
    manifest_type = str(data["type"])
    return OverlayManifest(
        id=manifest_id,
        type=manifest_type,
        path=path,
        data=data,
        stacks=tuple(_as_list(data.get("stacks", []))),
        requires={str(key): str(value) for key, value in dict(data.get("requires", {})).items()},
        conflicts=tuple(_as_list(data.get("conflicts", []))),
        checks=tuple(_as_list(data.get("checks", []))),
        python_dependencies=tuple(_as_list(data.get("python_dependencies", []))),
        npm_dependencies=tuple(_as_list(data.get("npm_dependencies", []))),
        npm_dev_dependencies=tuple(_as_list(data.get("npm_dev_dependencies", []))),
    )


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by template manifests.

    Supported shapes:

    - top-level `key: value`
    - top-level `key: []`
    - top-level lists using `key:` followed by `- value`
    - one-level maps using `key:` followed by `child: value`
    """

    result: dict[str, Any] = {}
    lines = [line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.startswith(" "):
            raise ValueError(f"Unexpected indentation in manifest: {line}")
        key, raw_value = _split_key_value(line)

        if raw_value:
            result[key] = _parse_scalar(raw_value)
            index += 1
            continue

        children: list[str] = []
        index += 1
        while index < len(lines) and lines[index].startswith("  "):
            children.append(lines[index][2:])
            index += 1

        result[key] = _parse_children(children)

    return result


def _parse_children(children: list[str]) -> Any:
    if not children:
        return {}
    if all(child.startswith("- ") for child in children):
        return [_parse_scalar(child[2:].strip()) for child in children]

    parsed: dict[str, Any] = {}
    for child in children:
        if child.startswith("- "):
            raise ValueError("Cannot mix list and map values in manifest")
        key, value = _split_key_value(child)
        parsed[key] = _parse_scalar(value) if value else {}
    return parsed


def _split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Expected key/value manifest line: {line}")
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value == "true":
        return True
    if value == "false":
        return False
    return value.strip('"')
