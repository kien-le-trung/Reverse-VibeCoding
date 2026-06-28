from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from reverse_vibecoding.template_composer import ComposeResult, TemplateLayer, compose_template_layers
from reverse_vibecoding.template_resolver import ResolvedTemplate, TemplateSelection, resolve_template_layers


DEFAULT_BACKEND_STACK = "fastapi"
DEFAULT_FRONTEND_STACK = "react_native"


@dataclass(frozen=True)
class InitProjectOptions:
    name: str
    backend_stack: str = DEFAULT_BACKEND_STACK
    frontend_stack: str = DEFAULT_FRONTEND_STACK
    domain: str = "todo_app"
    database: str = "sqlite"
    backend_level: str = "level_3"
    frontend_level: str = "level_3"
    templates_root: Path = Path("templates")
    sandbox_root: Path = Path("sandbox")
    force: bool = False
    setup_environment: bool = True
    mentor_prompt_path: Path = Path(".agents/prompts/mentor.md")


@dataclass(frozen=True)
class InitProjectResult:
    target: Path
    compose_result: ComposeResult
    backend: ResolvedTemplate
    frontend: ResolvedTemplate
    wiring_layer: TemplateLayer
    agent_files: tuple[Path, ...]
    setup_terminal_launched: bool


def init_project(
    options: InitProjectOptions,
    progress: Callable[[str], None] | None = None,
) -> InitProjectResult:
    """Generate a project into sandbox using resolved backend/frontend template layers."""

    target = options.sandbox_root / options.name
    _progress(progress, "check", f"Preparing target {target}")
    if target.exists() and not options.force:
        raise FileExistsError(f"Target directory already exists: {target}")

    _progress(progress, "resolve", f"Resolving backend stack {options.backend_stack}:{options.backend_level}")
    backend = resolve_template_layers(
        options.templates_root,
        TemplateSelection(
            stack=options.backend_stack,
            level=options.backend_level,
            domains=(options.domain,),
            databases=(options.database,),
        ),
    )
    _progress(progress, "resolve", f"Resolving frontend stack {options.frontend_stack}:{options.frontend_level}")
    frontend = resolve_template_layers(
        options.templates_root,
        TemplateSelection(
            stack=options.frontend_stack,
            level=options.frontend_level,
            domains=(options.domain,),
        ),
    )
    _progress(progress, "resolve", "Resolving full-stack wiring")
    wiring_layer = resolve_wiring_layer(options.templates_root, wiring_id(options.frontend_stack, options.backend_stack))

    _progress(progress, "compose", "Copying template layers")
    layers = [*backend.layers, *frontend.layers, wiring_layer]
    compose_result = compose_template_layers(layers, target)
    _progress(progress, "deps", "Writing dependency manifests")
    write_requirements(target, backend.python_dependencies)
    write_frontend_dependency_metadata(target, frontend)
    _progress(progress, "metadata", "Writing .rv metadata")
    write_project_metadata(options, target, backend, frontend, wiring_layer, compose_result)
    write_hidden_manifest(target)
    _progress(progress, "agent", "Writing project agent context")
    agent_files = write_agent_context(options, target, backend, frontend, compose_result)
    setup_terminal_launched = False
    if options.setup_environment:
        _progress(progress, "setup", "Launching setup terminal")
        setup_terminal_launched = launch_setup_terminal(target)
        if not setup_terminal_launched:
            _progress(progress, "setup", "Setup terminal is only supported automatically on Windows")
    else:
        _progress(progress, "setup", "Skipping setup terminal")

    return InitProjectResult(
        target=target,
        compose_result=compose_result,
        backend=backend,
        frontend=frontend,
        wiring_layer=wiring_layer,
        agent_files=agent_files,
        setup_terminal_launched=setup_terminal_launched,
    )


def resolve_wiring_layer(templates_root: Path, wiring_id: str) -> TemplateLayer:
    source = templates_root / "wiring" / wiring_id / "files"
    if not source.exists():
        raise FileNotFoundError(f"Wiring layer does not exist: {source}")
    return TemplateLayer(wiring_id, source)


def wiring_id(frontend_stack: str, backend_stack: str) -> str:
    return f"{frontend_stack}_{backend_stack}"


def write_requirements(target: Path, dependencies: tuple[str, ...]) -> None:
    if not dependencies:
        return
    requirements_path = target / "requirements.txt"
    existing = []
    if requirements_path.exists():
        existing = [
            line.strip()
            for line in requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    merged = list(dict.fromkeys((*existing, *dependencies)))
    requirements_path.write_text("\n".join(merged) + "\n", encoding="utf-8")


def write_frontend_dependency_metadata(target: Path, frontend: ResolvedTemplate) -> None:
    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "npm_dependencies": list(frontend.npm_dependencies),
        "npm_dev_dependencies": list(frontend.npm_dev_dependencies),
    }
    (rv_dir / "frontend_dependencies.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def launch_setup_terminal(target: Path) -> bool:
    """Open a terminal that creates venv and installs generated requirements."""

    if os.name != "nt":
        return False

    project_dir = str(target.resolve())
    escaped_project_dir = project_dir.replace("'", "''")
    command = (
        f"Set-Location -LiteralPath '{escaped_project_dir}'; "
        "Write-Host '[setup] Creating venv'; "
        "python -m venv venv; "
        "Write-Host '[setup] Installing requirements'; "
        ".\\venv\\Scripts\\python.exe -m pip install -r requirements.txt; "
        "Write-Host '[setup] Ready. Project environment is in .\\venv'"
    )

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=project_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return True


def _progress(callback: Callable[[str], None] | None, step: str, message: str) -> None:
    if callback is not None:
        callback(f"[init:{step}] {message}")


def write_agent_context(
    options: InitProjectOptions,
    target: Path,
    backend: ResolvedTemplate,
    frontend: ResolvedTemplate,
    compose_result: ComposeResult,
) -> tuple[Path, ...]:
    """Write project-specific agent context files under `.rv`.

    Generic mentor behavior lives once in `.agents/prompts/mentor.md`. These files only
    describe the generated project and the first task, so agents can start with a small
    context window and inspect code on demand.
    """

    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)

    task_files = write_task_files(target, options)
    file_map = build_file_map(target)
    task_path = target / ".rv" / "tasks" / "001_understand_repo.md"
    agent_context = render_agent_context(options, backend, frontend, compose_result, file_map)
    file_map_content = render_file_map(file_map)
    task_content = task_path.read_text(encoding="utf-8")
    mentor_prompt = read_mentor_prompt(options.mentor_prompt_path)
    files = {
        "agent_context.md": agent_context,
        "file_map.md": file_map_content,
        "agent_handoff.md": render_agent_handoff(
            options=options,
            mentor_prompt=mentor_prompt,
            agent_context=agent_context,
            task_content=task_content,
            file_map_content=file_map_content,
        ),
        "agent_handoff_short.md": render_agent_handoff_short(options),
    }

    written: list[Path] = []
    for filename, content in files.items():
        path = rv_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    written.extend(task_files)
    return tuple(written)


def read_mentor_prompt(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return """# Reverse Vibe Coding Mentor Prompt

You are mentoring a student in Reverse Vibe Coding. Ask questions, require tests, and guide engineering reasoning instead of solving the project directly.
""".strip()


def build_file_map(target: Path, *, limit: int = 48) -> tuple[str, ...]:
    ignored_parts = {"venv", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
    files: list[str] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(target)
        if any(part in ignored_parts for part in relative.parts):
            continue
        if relative.parts[0] == ".rv" and relative.parts[1:2] != ("tasks",) and relative.name != "project.json":
            continue
        files.append(relative.as_posix())
        if len(files) >= limit:
            break
    return tuple(files)


def render_agent_context(
    options: InitProjectOptions,
    backend: ResolvedTemplate,
    frontend: ResolvedTemplate,
    compose_result: ComposeResult,
    file_map: tuple[str, ...],
) -> str:
    important_files = "\n".join(f"- {path}" for path in file_map[:24])
    layers = "\n".join(f"- {layer}" for layer in compose_result.applied_layers)
    checks = "\n".join(f"- {check}" for check in dict.fromkeys((*backend.checks, *frontend.checks)))

    return f"""# Project Agent Context

Project: {options.name}
Domain: {options.domain}
Database: {options.database}
Backend: {options.backend_stack} ({options.backend_level})
Frontend: {options.frontend_stack} ({options.frontend_level})

Generated folders:
- backend/
- mobile/
- .rv/

Applied layers:
{layers}

Suggested checks:
{checks}

Important files:
{important_files}

Use this file as project context only. Generic mentor behavior lives in `.agents/prompts/mentor.md`.
"""


def write_task_files(target: Path, options: InitProjectOptions) -> tuple[Path, ...]:
    tasks_dir = target / ".rv" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "README.md": render_tasks_readme(),
        "001_understand_repo.md": render_initial_task(options),
    }

    written: list[Path] = []
    for filename, content in files.items():
        path = tasks_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return tuple(written)


def render_tasks_readme() -> str:
    return """# Learning Tasks

This directory tracks the student's learning work from start to finish.

Task files should be small and concrete. Add new files as the mentor creates follow-up work.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`
- `004_reflect.md`

Each task should include:

- goal
- student actions
- evidence expected
- mentor review focus
"""


def render_initial_task(options: InitProjectOptions) -> str:
    return f"""# Task 001: Understand The Repo

Task: Understand and verify the generated {options.domain} project.

Student should:
1. Confirm the setup terminal completed successfully or run setup manually.
2. Run backend tests.
3. Inspect the API route and repository boundaries.
4. Inspect how the mobile app calls the backend.
5. Explain one missing test, edge case, or design improvement.

Mentor instruction:
- Do not implement the task directly.
- Ask what the student has run so far.
- Ask the student to explain their repo understanding before explaining it yourself.
- Refine the student's explanation from an abstract architecture level.
- Require test evidence before accepting conclusions.
- When this task is complete, propose the next task and add or ask the student to add it under `.rv/tasks/`.
"""


def render_file_map(file_map: tuple[str, ...]) -> str:
    entries = "\n".join(f"- {path}" for path in file_map)
    return f"""# File Map

This is a compact map of generated project files. Inspect files on demand instead of loading the whole project at once.

{entries}
"""


def render_agent_handoff(
    *,
    options: InitProjectOptions,
    mentor_prompt: str,
    agent_context: str,
    task_content: str,
    file_map_content: str,
) -> str:
    return f"""# Agent Handoff

Read this file first and begin mentoring immediately.

Your first response should:

1. Acknowledge the project context briefly.
2. Ask the student to explain their current understanding of the repo.
3. Ask what setup/tests they have already run.
4. Use `.rv/tasks/001_understand_repo.md` as the active task.

Do not implement the project for the student unless they ask for a very small illustrative snippet.

---

{mentor_prompt}

---

{agent_context.strip()}

---

{task_content.strip()}

---

{file_map_content.strip()}

---

Project path: sandbox/{options.name}
"""


def render_agent_handoff_short(options: InitProjectOptions) -> str:
    return f"""# Short Agent Handoff

Paste this into your IDE agent when context is limited.

You are mentoring a Reverse Vibe Coding student. Do not solve the project directly. Ask questions, require tests, and guide engineering reasoning.

Project: {options.name}
Domain: {options.domain}
Backend: {options.backend_stack} {options.backend_level}
Frontend: {options.frontend_stack} {options.frontend_level}
Database: {options.database}

Current task: understand and verify the generated app. Start by asking what the student has run so far.

Task tracking: read `.rv/tasks/001_understand_repo.md` first. Keep future learning work in `.rv/tasks/`.
"""


def write_project_metadata(
    options: InitProjectOptions,
    target: Path,
    backend: ResolvedTemplate,
    frontend: ResolvedTemplate,
    wiring_layer: TemplateLayer,
    compose_result: ComposeResult,
) -> None:
    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "name": options.name,
        "domain": options.domain,
        "database": options.database,
        "backend": {
            "stack": options.backend_stack,
            "level": options.backend_level,
            "manifests": list(backend.manifest_ids),
            "python_dependencies": list(backend.python_dependencies),
        },
        "frontend": {
            "stack": options.frontend_stack,
            "level": options.frontend_level,
            "manifests": list(frontend.manifest_ids),
            "npm_dependencies": list(frontend.npm_dependencies),
            "npm_dev_dependencies": list(frontend.npm_dev_dependencies),
        },
        "wiring": wiring_layer.id,
        "layers": list(compose_result.applied_layers),
        "checks": list(dict.fromkeys((*backend.checks, *frontend.checks))),
    }

    (rv_dir / "project.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_hidden_manifest(target: Path) -> None:
    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)
    hidden_manifest = {
        "hidden_tests": [],
        "bug_seeds": [],
        "notes": "Generated by rv init. Hidden assessment assets are not implemented yet.",
    }
    (rv_dir / "hidden_manifest.json").write_text(
        json.dumps(hidden_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
