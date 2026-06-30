from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from reverse_vibecoding.bug_seeds import AppliedBugSeed, apply_random_bug_seeds
from reverse_vibecoding.template_composer import ComposeResult, TemplateLayer, compose_template_layers
from reverse_vibecoding.template_resolver import LEVEL_ORDER, ResolvedTemplate, TemplateSelection, resolve_template_layers


DEFAULT_BACKEND_STACK = "fastapi"
DEFAULT_FRONTEND_STACK = "react_native"
NO_DOMAIN = "no_domain"
NO_DATABASE = "no_database"

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
    mentor_prompt_path: Path = Path(".agents/global_prompt.md")
    mentor_guardrails_path: Path = Path(".agents/global_guardrails.md")
    bug_seed_count: int = 0
    bug_seed_random_seed: int | None = None
    bug_categories: tuple[str, ...] = ()
    bug_hidden: bool = False


@dataclass(frozen=True)
class InitProjectResult:
    target: Path
    compose_result: ComposeResult
    backend: ResolvedTemplate
    frontend: ResolvedTemplate
    wiring_layer: TemplateLayer
    agent_files: tuple[Path, ...]
    project_opened: bool
    setup_process_launched: bool
    bug_seeds: tuple[AppliedBugSeed, ...]


@dataclass(frozen=True)
class ImportProjectOptions:
    target: Path
    agents_root: Path = Path(".agents")
    mentor_prompt_path: Path = Path(".agents/global_prompt.md")
    mentor_guardrails_path: Path = Path(".agents/global_guardrails.md")


@dataclass(frozen=True)
class ImportProjectResult:
    target: Path
    agent_files: tuple[Path, ...]


@dataclass(frozen=True)
class DoctorOptions:
    agents_root: Path = Path(".agents")
    templates_root: Path = Path("templates")
    sandbox_root: Path = Path("sandbox")
    minimum_python: tuple[int, int] = (3, 11)


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    required: bool
    message: str


@dataclass(frozen=True)
class DoctorResult:
    checks: tuple[DoctorCheck, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks if check.required)


@dataclass(frozen=True)
class OpenProjectResult:
    target: Path
    opened: bool
    handoff_path: Path
    short_handoff_path: Path


def init_project(
    options: InitProjectOptions,
    progress: Callable[[str], None] | None = None,
) -> InitProjectResult:
    """Generate a project into sandbox using resolved backend/frontend template layers."""

    target = options.sandbox_root / options.name
    _progress(progress, "check", f"Preparing target {target}")
    if target.exists() and not options.force:
        raise FileExistsError(f"Target directory already exists: {target}")
    validate_init_options(options)

    _progress(progress, "resolve", f"Resolving backend stack {options.backend_stack}:{options.backend_level}")
    domain_overlays = selected_domain_overlays(options.domain)
    database_overlays = selected_database_overlays(options.database)
    backend = resolve_template_layers(
        options.templates_root,
        TemplateSelection(
            stack=options.backend_stack,
            level=options.backend_level,
            domains=domain_overlays,
            databases=database_overlays,
        ),
    )
    _progress(progress, "resolve", f"Resolving frontend stack {options.frontend_stack}:{options.frontend_level}")
    frontend = resolve_template_layers(
        options.templates_root,
        TemplateSelection(
            stack=options.frontend_stack,
            level=options.frontend_level,
            domains=domain_overlays,
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
    _progress(progress, "bugs", "Applying controlled bug seeds")
    bug_seeds = apply_random_bug_seeds(
        target=target,
        backend_stack=options.backend_stack,
        frontend_stack=options.frontend_stack,
        count=options.bug_seed_count,
        seed=options.bug_seed_random_seed,
        categories=options.bug_categories,
    )
    _progress(progress, "metadata", "Writing .rv metadata")
    write_project_metadata(options, target, backend, frontend, wiring_layer, compose_result, bug_seeds)
    write_hidden_manifest(target, bug_seeds, bug_hidden=options.bug_hidden)
    _progress(progress, "agent", "Writing project agent context")
    agent_files = write_agent_context(options, target, backend, frontend, compose_result)
    project_opened = False
    setup_process_launched = False
    if options.setup_environment:
        _progress(progress, "setup", "Opening generated project in VS Code")
        project_opened = open_project_in_editor(target)
        if not project_opened:
            _progress(progress, "setup", "VS Code CLI not found on PATH; open the generated project manually")
        _progress(progress, "setup", "Starting dependency installation")
        setup_process_launched = launch_dependency_setup(target)
        if not setup_process_launched:
            _progress(progress, "setup", "Automatic dependency setup is only supported on Windows")
    else:
        _progress(progress, "setup", "Skipping project open and dependency setup")

    return InitProjectResult(
        target=target,
        compose_result=compose_result,
        backend=backend,
        frontend=frontend,
        wiring_layer=wiring_layer,
        agent_files=agent_files,
        project_opened=project_opened,
        setup_process_launched=setup_process_launched,
        bug_seeds=bug_seeds,
    )


def import_project(
    options: ImportProjectOptions,
    progress: Callable[[str], None] | None = None,
) -> ImportProjectResult:
    """Install reverse-vibecoding agent files into an existing project."""

    target = options.target.expanduser()
    _progress(progress, "import", f"Preparing target {target}")
    if not target.is_absolute():
        raise ValueError(f"Import target must be an absolute path: {target}")
    if not target.exists():
        raise FileNotFoundError(f"Import target does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Import target is not a directory: {target}")

    _progress(progress, "import", "Copying agent prompts, schemas, and rubrics")
    copied_agent_files = copy_agent_support_files(options.agents_root, target)
    _progress(progress, "import", "Writing .rv task and handoff files")
    agent_files = write_agent_context(options, target)
    _progress(progress, "import", "Import complete")
    return ImportProjectResult(target=target, agent_files=tuple((*copied_agent_files, *agent_files)))


def doctor(
    options: DoctorOptions = DoctorOptions(),
    *,
    command_resolver: Callable[[str], str | None] = shutil.which,
    python_version: Sequence[int] = sys.version_info,
) -> DoctorResult:
    """Check whether the local environment can support common rev-vib workflows."""

    checks: list[DoctorCheck] = []
    minimum_python = options.minimum_python
    current_python = tuple(python_version[:2])
    checks.append(
        DoctorCheck(
            name="python",
            ok=current_python >= minimum_python,
            required=True,
            message=(
                f"Python {current_python[0]}.{current_python[1]} detected; "
                f"requires {minimum_python[0]}.{minimum_python[1]}+"
            ),
        )
    )

    checks.extend(
        [
            _path_check("agents", options.agents_root, required=True, kind="dir"),
            _path_check("global_prompt", options.agents_root / "global_prompt.md", required=True, kind="file"),
            _path_check("global_guardrails", options.agents_root / "global_guardrails.md", required=True, kind="file"),
            _path_check("task_schema", options.agents_root / "schemas" / "task.schema.yaml", required=True, kind="file"),
            _path_check(
                "progress_schema",
                options.agents_root / "schemas" / "progress.schema.yaml",
                required=True,
                kind="file",
            ),
            _path_check(
                "engineering_review_rubric",
                options.agents_root / "rubrics" / "engineering_review.md",
                required=True,
                kind="file",
            ),
            _path_check("templates", options.templates_root, required=True, kind="dir"),
            _sandbox_check(options.sandbox_root),
        ]
    )

    for command, required in (
        ("code", False),
        ("node", False),
        ("npm", False),
        ("mvn", False),
    ):
        resolved = command_resolver(command)
        checks.append(
            DoctorCheck(
                name=command,
                ok=resolved is not None,
                required=required,
                message=f"{command} found at {resolved}" if resolved else f"{command} not found on PATH",
            )
        )

    return DoctorResult(checks=tuple(checks))


def open_project(project: Path, *, sandbox_root: Path = Path("sandbox")) -> OpenProjectResult:
    target = resolve_project_target(project, sandbox_root=sandbox_root)
    handoff_path = target / ".rv" / "agent_handoff.md"
    short_handoff_path = target / ".rv" / "agent_handoff_short.md"
    opened = open_project_in_editor(target)
    return OpenProjectResult(
        target=target,
        opened=opened,
        handoff_path=handoff_path,
        short_handoff_path=short_handoff_path,
    )


def resolve_project_target(project: Path, *, sandbox_root: Path = Path("sandbox")) -> Path:
    expanded = project.expanduser()
    if expanded.exists():
        target = expanded
    elif len(expanded.parts) == 1:
        target = sandbox_root / expanded
    else:
        target = expanded

    if not target.exists():
        raise FileNotFoundError(f"Project does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Project is not a directory: {target}")
    return target.resolve()


def _path_check(name: str, path: Path, *, required: bool, kind: str) -> DoctorCheck:
    if kind == "dir":
        ok = path.is_dir()
        expected = "directory"
    elif kind == "file":
        ok = path.is_file()
        expected = "file"
    else:
        raise ValueError(f"Unsupported path check kind: {kind}")

    return DoctorCheck(
        name=name,
        ok=ok,
        required=required,
        message=f"{expected} found: {path}" if ok else f"Missing {expected}: {path}",
    )


def _sandbox_check(path: Path) -> DoctorCheck:
    if not path.exists():
        return DoctorCheck(
            name="sandbox",
            ok=False,
            required=True,
            message=f"Sandbox directory does not exist: {path}",
        )
    if not path.is_dir():
        return DoctorCheck(
            name="sandbox",
            ok=False,
            required=True,
            message=f"Sandbox path is not a directory: {path}",
        )
    writable = os.access(path, os.W_OK)
    return DoctorCheck(
        name="sandbox",
        ok=writable,
        required=True,
        message=f"Sandbox directory is writable: {path}" if writable else f"Sandbox directory is not writable: {path}",
    )


def resolve_wiring_layer(templates_root: Path, wiring_id: str) -> TemplateLayer:
    source = templates_root / "wiring" / wiring_id / "files"
    if not source.exists():
        raise FileNotFoundError(f"Wiring layer does not exist: {source}")
    return TemplateLayer(wiring_id, source)


def wiring_id(frontend_stack: str, backend_stack: str) -> str:
    return f"{frontend_stack}_{backend_stack}"


def validate_init_options(options: InitProjectOptions) -> None:
    conflicts: list[str] = []
    if options.domain != NO_DOMAIN:
        if _level_index(options.backend_stack, options.backend_level) < _level_index(options.backend_stack, "level_2"):
            conflicts.append(
                f"--backend-level {options.backend_level} cannot be combined with --domain {options.domain}; "
                f"use --domain {NO_DOMAIN} or choose backend level_2+"
            )
        if _level_index(options.frontend_stack, options.frontend_level) < _level_index(options.frontend_stack, "level_2"):
            conflicts.append(
                f"--frontend-level {options.frontend_level} cannot be combined with --domain {options.domain}; "
                f"use --domain {NO_DOMAIN} or choose frontend level_2+"
            )
    if options.database != NO_DATABASE and _level_index(options.backend_stack, options.backend_level) < _level_index(
        options.backend_stack,
        "level_3",
    ):
        conflicts.append(
            f"--backend-level {options.backend_level} cannot be combined with --database {options.database}; "
            f"use --database {NO_DATABASE} or choose backend level_3+"
        )
    if conflicts:
        raise ValueError("Conflicting init options: " + " ".join(conflicts))


def _level_index(stack: str, level: str) -> int:
    try:
        return LEVEL_ORDER[stack].index(level)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unsupported level {level!r} for stack {stack!r}") from exc


def selected_domain_overlays(domain: str) -> tuple[str, ...]:
    if domain == NO_DOMAIN:
        return ()
    return (domain,)


def selected_database_overlays(database: str) -> tuple[str, ...]:
    if database == NO_DATABASE:
        return ()
    return (database,)


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


def open_project_in_editor(target: Path) -> bool:
    """Open the generated project in a new VS Code window when the CLI is available."""

    editor = shutil.which("code")
    if editor is None:
        return False

    project_dir = str(target.resolve())
    subprocess.Popen([editor, "-n", project_dir], cwd=project_dir)
    return True


def launch_dependency_setup(target: Path) -> bool:
    """Install generated project dependencies in a background setup process."""

    if os.name != "nt":
        return False

    project_dir = str(target.resolve())
    log_path = target / ".rv" / "setup.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    command = render_dependency_setup_command(Path(project_dir))

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=project_dir,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    log_file.close()
    return True


def render_dependency_setup_command(target: Path) -> str:
    escaped_project_dir = str(target.resolve()).replace("'", "''")
    return (
        f"Set-Location -LiteralPath '{escaped_project_dir}'; "
        "Write-Host '[setup] Project setup started'; "
        "Write-Host '[setup] Creating venv'; "
        "python -m venv venv; "
        "Write-Host '[setup] Activating venv'; "
        ". .\\venv\\Scripts\\Activate.ps1; "
        "if (Test-Path requirements.txt) { "
        "Write-Host '[setup] Installing Python requirements into active venv'; "
        "python -m pip install -r requirements.txt; "
        "} "
        "if (Test-Path backend\\package.json) { "
        "Write-Host '[setup] Installing backend Node packages'; "
        "Push-Location backend; npm install; Pop-Location; "
        "} "
        "if (Test-Path backend\\pom.xml) { "
        "if (Get-Command mvn -ErrorAction SilentlyContinue) { "
        "Write-Host '[setup] Resolving Maven dependencies'; "
        "Push-Location backend; mvn dependency:go-offline; Pop-Location; "
        "} else { "
        "Write-Host '[setup] Maven not found on PATH; skipping Maven dependency prefetch'; "
        "} "
        "} "
        "if (Test-Path mobile\\package.json) { "
        "Write-Host '[setup] Installing frontend packages'; "
        "Push-Location mobile; npm install; Pop-Location; "
        "} "
        "Write-Host '[setup] Ready. Dependency setup complete.'"
    )


def _progress(callback: Callable[[str], None] | None, step: str, message: str) -> None:
    if callback is not None:
        callback(f"[init:{step}] {message}")


def write_agent_context(
    options: InitProjectOptions | ImportProjectOptions,
    target: Path,
    backend: ResolvedTemplate | None = None,
    frontend: ResolvedTemplate | None = None,
    compose_result: ComposeResult | None = None,
) -> tuple[Path, ...]:
    """Write project-specific agent context files under `.rv`.

    Generic operator behavior lives once in `.agents/global_prompt.md`. These files only
    describe the generated project and the first task, so agents can start with a small
    context window and inspect code on demand.
    """

    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)

    task_files = write_task_files(target, options)
    progress_files = write_progress_files(target)
    file_map = build_file_map(target)
    task_path = target / ".rv" / "tasks" / "001_understand_repo.md"
    agent_context = render_agent_context(options, backend, frontend, compose_result, file_map, target=target)
    file_map_content = render_file_map(file_map)
    task_content = task_path.read_text(encoding="utf-8")
    mentor_prompt = read_mentor_prompt(options.mentor_prompt_path)
    mentor_guardrails = options.mentor_guardrails_path.read_text(encoding="utf-8").strip()
    files = {
        "agent_context.md": agent_context,
        "file_map.md": file_map_content,
        "agent_handoff.md": render_agent_handoff(
            options=options,
            target=target,
            mentor_prompt=mentor_prompt,
            mentor_guardrails=mentor_guardrails,
            agent_context=agent_context,
            task_content=task_content,
            file_map_content=file_map_content,
        ),
        "agent_handoff_short.md": render_agent_handoff_short(options, target=target),
    }
    if isinstance(options, ImportProjectOptions):
        files["project.json"] = json.dumps(
            {
                "name": target.name,
                "mode": "imported",
                "path": str(target),
                "notes": "Imported by rev-vib import. Stack and run commands should be inferred from the repository.",
            },
            indent=2,
            sort_keys=True,
        ) + "\n"

    written: list[Path] = []
    for filename, content in files.items():
        path = rv_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    written.extend(write_native_instruction_files(target, mentor_prompt, mentor_guardrails))
    written.extend(task_files)
    written.extend(progress_files)
    return tuple(written)


def copy_agent_support_files(agents_root: Path, target: Path) -> tuple[Path, ...]:
    source = agents_root.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Agent support directory does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Agent support path is not a directory: {source}")

    destination = (target / ".agents").resolve()
    if source == destination:
        return tuple(path for path in sorted(destination.rglob("*")) if path.is_file())

    shutil.copytree(source, destination, dirs_exist_ok=True)
    return tuple(path for path in sorted(destination.rglob("*")) if path.is_file())


def read_mentor_prompt(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return """# Reverse VibeCoding Operator Prompt

You are the operator/reviewer in a reverse-vibecoding workflow. The user implements all code changes. Ask the user for implementation, collect evidence from files/diffs/commands when possible, and review the result. You own `.rv/tasks/` and `.rv/progress/` logging. Do not edit project files yourself.
""".strip()


def write_native_instruction_files(target: Path, mentor_prompt: str, mentor_guardrails: str) -> tuple[Path, ...]:
    github_dir = target / ".github"
    instructions_dir = github_dir / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    native_prompt = render_native_instruction_prompt(mentor_prompt, mentor_guardrails)
    files = {
        "AGENTS.md": native_prompt,
        "CLAUDE.md": native_prompt,
        ".github/copilot-instructions.md": native_prompt,
        ".github/instructions/reverse-vibecoding.instructions.md": native_prompt,
    }

    written: list[Path] = []
    for relative_path, content in files.items():
        path = target / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return tuple(written)


def render_native_instruction_prompt(mentor_prompt: str, mentor_guardrails: str) -> str:
    return f"""# Reverse VibeCoding Instructions

{mentor_guardrails.strip()}

---

{mentor_prompt.strip()}
"""


def build_file_map(target: Path, *, limit: int = 48) -> tuple[str, ...]:
    ignored_parts = {"venv", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".agents"}
    files: list[str] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(target)
        if any(part in ignored_parts for part in relative.parts):
            continue
        if (
            relative.parts[0] == ".rv"
            and relative.parts[1:2] not in {("tasks",), ("progress",)}
            and relative.name != "project.json"
        ):
            continue
        files.append(relative.as_posix())
        if len(files) >= limit:
            break
    return tuple(files)


def render_agent_context(
    options: InitProjectOptions | ImportProjectOptions,
    backend: ResolvedTemplate | None,
    frontend: ResolvedTemplate | None,
    compose_result: ComposeResult | None,
    file_map: tuple[str, ...],
    *,
    target: Path,
) -> str:
    important_files = "\n".join(f"- {path}" for path in file_map[:24])
    if not important_files:
        important_files = "- No source files found yet."

    if isinstance(options, ImportProjectOptions):
        return f"""# Project Agent Context

Project: {target.name}
Mode: imported existing project
Project path: {target}

Imported workflow folders:
- .agents/
- .rv/

Important files:
{important_files}

This project was imported into the reverse-vibecoding workflow. Infer the stack, architecture, tests, and run commands from the repository itself before assigning implementation work.

Use this file as project context only. Generic operator behavior lives in `.agents/global_prompt.md`, and per-response guardrails live in `.agents/global_guardrails.md`.
"""

    if backend is None or frontend is None or compose_result is None:
        raise ValueError("Generated project context requires backend, frontend, and compose_result")

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

Use this file as project context only. Generic operator behavior lives in `.agents/global_prompt.md`, and per-response guardrails live in `.agents/global_guardrails.md`.
"""


def write_task_files(target: Path, options: InitProjectOptions | ImportProjectOptions) -> tuple[Path, ...]:
    tasks_dir = target / ".rv" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "README.md": render_tasks_readme(),
        "001_understand_repo.md": render_initial_task(options, target=target),
    }

    written: list[Path] = []
    for filename, content in files.items():
        path = tasks_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return tuple(written)


def write_progress_files(target: Path) -> tuple[Path, ...]:
    progress_dir = target / ".rv" / "progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    path = progress_dir / "README.md"
    path.write_text(render_progress_readme(), encoding="utf-8")
    return (path,)


def render_tasks_readme() -> str:
    return """# Reverse VibeCoding Tasks

This directory tracks implementation requests from the operator to the user.

Task files should be small and concrete. The operator creates or updates files here as follow-up work is chosen.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`
- `004_reflect.md`

Each task should include:

- request
- expected behavior
- implementation scope
- acceptance criteria
- evidence required

When creating or updating task files, read `.agents/schemas/task.schema.yaml` and keep the YAML front matter aligned with it.

When a task is complete, the operator adds or updates a matching progress entry under `.rv/progress/`.
"""


def render_progress_readme() -> str:
    return """# Reverse VibeCoding Progress

This directory records what the user changed, what evidence was reviewed, and what follow-up work remains.

Progress entries should be written by the operator after review, not before implementation. Do not ask the user to maintain these logs; ask only for missing facts or evidence that cannot be inspected directly.

When creating or updating progress files, read `.agents/schemas/progress.schema.yaml` and keep the YAML front matter aligned with it.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`

Each progress entry should include:

- task or feature completed
- what the user changed or investigated
- acceptance status
- concepts explained, if any
- evidence reviewed, such as code paths, commands, screenshots, or tests
- mistakes, rework, or design tradeoffs discussed
- remaining gaps or next implementation target
"""


def render_initial_task(options: InitProjectOptions | ImportProjectOptions, *, target: Path) -> str:
    if isinstance(options, ImportProjectOptions):
        return f"""---
id: "001_understand_repo"
title: "Understand the imported repo"
status: active
request: "Inspect and summarize the imported {target.name} project so the next implementation request is grounded in the repo."
expected_behavior:
  - "The user can identify the project's main responsibilities and runtime entry points."
  - "The user can name one missing test, edge case, or design improvement."
implementation_scope:
  - "Inspect files only; do not change product code for this task."
acceptance_criteria:
  - "The user summarizes the project structure accurately."
  - "The user identifies one concrete follow-up implementation target."
evidence_required:
  - "Short explanation of the project's main components."
  - "Notes from inspecting key source, configuration, and test files."
context:
  - "Infer stack, test commands, and run commands from the imported repository."
  - "Inspect README, package manifests, dependency files, entry points, and tests."
  - "Explain one missing test, edge case, or design improvement."
review_focus:
  - "Repo understanding."
  - "Architecture and runtime boundaries."
  - "Missing test or edge-case identification."
---

# Task 001: Understand The Imported Repo

Request: Inspect and summarize the imported {target.name} project so the next implementation request is grounded in the repo.

User should:
1. Identify the project's stack, entry points, and expected setup or test commands.
2. Inspect the main source and test boundaries.
3. Explain one missing test, edge case, or design improvement.

Operator instruction:
- Before each response, apply `.agents/global_guardrails.md`.
- Do not edit project files or implement the task directly.
- Inspect available files, diffs, and task/progress logs before asking the user for context.
- Ask the user to explain repo understanding only when it is needed for review or cannot be inferred from available evidence.
- You may explain abstract architecture concepts if that helps clarify the next request.
- Collect evidence yourself when possible; ask for evidence only when you cannot inspect or run it directly.
- When this task is complete, propose the next implementation request and add it under `.rv/tasks/`.
- After this task is reviewed, add a matching progress entry under `.rv/progress/`.
- Before updating `.rv/tasks/` or `.rv/progress/`, read the matching YAML schema in `.agents/schemas/`.
"""

    return f"""---
id: "001_understand_repo"
title: "Understand the repo"
status: active
request: "Inspect and summarize the generated {options.domain} project so the next implementation request is grounded in the repo."
expected_behavior:
  - "The user can identify the backend and frontend responsibilities."
  - "The user can name one missing test, edge case, or design improvement."
implementation_scope:
  - "Inspect files only; do not change product code for this task."
acceptance_criteria:
  - "The user summarizes backend and frontend wiring accurately."
  - "The user identifies one concrete follow-up implementation target."
evidence_required:
  - "Short explanation of backend and mobile responsibilities."
  - "Notes from inspecting the key backend and mobile files."
context:
  - "Confirm `.rv/setup.log` shows dependency setup completed successfully or run backend and frontend setup manually."
  - "Inspect the backend setup and identify what API tests are missing."
  - "Inspect the API route and repository boundaries."
  - "Inspect how the mobile app calls the backend."
  - "Explain one missing test, edge case, or design improvement."
review_focus:
  - "Repo understanding."
  - "Backend route and repository boundaries."
  - "Missing API test or edge-case identification."
files_to_inspect:
  - "backend/app/main.py"
  - "backend/app/api/routes/todos.py"
  - "backend/app/repositories/todo_repository.py"
  - "mobile/src/api/client.ts"
  - "mobile/src/features/todos/TodoList.tsx"
---

# Task 001: Understand The Repo

Request: Inspect and summarize the generated {options.domain} project so the next implementation request is grounded in the repo.

User should:
1. Confirm `.rv/setup.log` shows dependency setup completed successfully or run backend and frontend setup manually.
2. Inspect the backend setup and identify what API tests are missing.
3. Inspect the API route and repository boundaries.
4. Inspect how the mobile app calls the backend.
5. Explain one missing test, edge case, or design improvement.

Operator instruction:
- Before each response, apply `.agents/global_guardrails.md`.
- Do not edit project files or implement the task directly.
- Inspect available files, diffs, and task/progress logs before asking the user for context.
- Ask the user to explain repo understanding only when it is needed for review or cannot be inferred from available evidence.
- You may explain abstract architecture concepts if that helps clarify the next request.
- Collect evidence yourself when possible; ask for evidence only when you cannot inspect or run it directly.
- When this task is complete, propose the next implementation request and add it under `.rv/tasks/`.
- After this task is reviewed, add a matching progress entry under `.rv/progress/`.
- Before updating `.rv/tasks/` or `.rv/progress/`, read the matching YAML schema in `.agents/schemas/`.
"""


def render_file_map(file_map: tuple[str, ...]) -> str:
    entries = "\n".join(f"- {path}" for path in file_map)
    return f"""# File Map

This is a compact map of generated project files. Inspect files on demand instead of loading the whole project at once.

{entries}
"""


def render_agent_handoff(
    *,
    options: InitProjectOptions | ImportProjectOptions,
    target: Path,
    mentor_prompt: str,
    mentor_guardrails: str,
    agent_context: str,
    task_content: str,
    file_map_content: str,
) -> str:
    context_line = "Acknowledge the imported project context briefly." if isinstance(
        options,
        ImportProjectOptions,
    ) else "Acknowledge the project context briefly."
    project_path = str(target) if isinstance(options, ImportProjectOptions) else f"sandbox/{options.name}"
    return f"""# Agent Handoff

Read this file first and begin the reverse-vibecoding workflow immediately.

Your first response should:

1. Read `.agents/global_guardrails.md` and apply it before every response.
2. {context_line}
3. Inspect the current task, progress logs, repo state, and any user-provided context.
4. Ask the user for missing context only when it cannot be inferred from files, diffs, commands, or prior logs.
5. Use `.rv/tasks/001_understand_repo.md` as the active task.
6. Update `.rv/tasks/` when assigning work and `.rv/progress/` after review to track what you asked for, what the user did, and what evidence was reviewed.
7. Read `.agents/schemas/task.schema.yaml` before updating `.rv/tasks/`.
8. Read `.agents/schemas/progress.schema.yaml` before updating `.rv/progress/`.

Do not edit project files or implement the project yourself. If code must change, ask the user to implement it. You may explain abstract concepts and provide tiny illustrative snippets in chat when helpful.

---

{mentor_guardrails.strip()}

---

{mentor_prompt}

---

{agent_context.strip()}

---

{task_content.strip()}

---

{file_map_content.strip()}

---

Project path: {project_path}
"""


def render_agent_handoff_short(options: InitProjectOptions | ImportProjectOptions, *, target: Path) -> str:
    if isinstance(options, ImportProjectOptions):
        project_details = f"""Project: {target.name}
Mode: imported existing project
Path: {target}"""
        current_task = "understand and verify the imported repo"
    else:
        project_details = f"""Project: {options.name}
Domain: {options.domain}
Backend: {options.backend_stack} {options.backend_level}
Frontend: {options.frontend_stack} {options.frontend_level}
Database: {options.database}"""
        current_task = "understand and verify the generated app"

    return f"""# Short Agent Handoff

Paste this into your IDE agent when context is limited.

You are the operator/reviewer in a reverse-vibecoding workflow. The user implements all code changes. Do not edit project files or solve the project yourself; ask the user to implement.

{project_details}

Current task: {current_task}. Start by inspecting `.rv/tasks/`, `.rv/progress/`, source files, diffs, and any user-provided context before asking for missing information.

Guardrails: read `.agents/global_guardrails.md` first and apply it before every response. Do not edit project files or implement yourself.

Code review: before evaluating user-written code, read `.agents/rubrics/engineering_review.md` and apply it.

Schemas: read `.agents/schemas/task.schema.yaml` before updating `.rv/tasks/`, and read `.agents/schemas/progress.schema.yaml` before updating `.rv/progress/`.

Task tracking: read `.rv/tasks/001_understand_repo.md` next. You maintain future implementation requests in `.rv/tasks/` and completed work summaries in `.rv/progress/`; do not ask the user to maintain those logs.
"""


def write_project_metadata(
    options: InitProjectOptions,
    target: Path,
    backend: ResolvedTemplate,
    frontend: ResolvedTemplate,
    wiring_layer: TemplateLayer,
    compose_result: ComposeResult,
    bug_seeds: tuple[AppliedBugSeed, ...],
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
            "npm_dependencies": list(backend.npm_dependencies),
            "npm_dev_dependencies": list(backend.npm_dev_dependencies),
            "maven_dependencies": list(backend.maven_dependencies),
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
        "bug_seed_count": len(bug_seeds),
        "bug_hidden": options.bug_hidden,
    }

    (rv_dir / "project.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_hidden_manifest(
    target: Path,
    bug_seeds: tuple[AppliedBugSeed, ...],
    *,
    bug_hidden: bool,
) -> None:
    rv_dir = target / ".rv"
    rv_dir.mkdir(parents=True, exist_ok=True)
    hidden_manifest = {
        "hidden_tests": [],
        "bug_hidden": bug_hidden,
        "bug_seeds": [
            _render_hidden_bug_seed(bug_seed, hidden=bug_hidden, index=index)
            for index, bug_seed in enumerate(bug_seeds, start=1)
        ],
        "notes": "Generated by rev-vib init. Bug seed details may be hidden depending on bug_hidden.",
    }
    (rv_dir / "hidden_manifest.json").write_text(
        json.dumps(hidden_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _render_hidden_bug_seed(
    bug_seed: AppliedBugSeed,
    *,
    hidden: bool,
    index: int,
) -> dict[str, str | bool]:
    if hidden:
        return {
            "id": f"hidden_bug_{index}",
            "hidden": True,
            "files_changed": "hidden",
            "note": "Bug type and target are hidden. Inspect the repo behavior to identify it.",
        }
    return {
        "id": bug_seed.id,
        "hidden": False,
        "category": bug_seed.category,
        "file_changed": bug_seed.relative_path,
        "learning_goal": bug_seed.learning_goal,
        "description": bug_seed.description,
    }
