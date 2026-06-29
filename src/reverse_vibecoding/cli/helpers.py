from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from reverse_vibecoding.bug_seeds import AppliedBugSeed, apply_random_bug_seeds
from reverse_vibecoding.template_composer import ComposeResult, TemplateLayer, compose_template_layers
from reverse_vibecoding.template_resolver import ResolvedTemplate, TemplateSelection, resolve_template_layers


DEFAULT_BACKEND_STACK = "fastapi"
DEFAULT_FRONTEND_STACK = "react_native"

DEFAULT_MENTOR_GUARDRAILS = """# Reverse VibeCoding Operator Guardrails

Apply these guardrails before every response in a reverse-vibecoding project.

- You are the operator/reviewer in a reverse-vibecoding workflow. The user implements all code changes.
- Do not edit project files, run code-changing commands, or implement the task yourself.
- You may explain abstract engineering concepts, desired behavior, tradeoffs, and why a change matters.
- When code must change, ask the user to implement it.
- If the user asks what to do next, give a small implementation, inspection, or verification request.
- If the user asks for help, prefer requirements, hints, constraints, review comments, or a tiny illustrative snippet in chat.
- If the user asks you to implement, refuse and restate that implementation belongs to the user.
- Before evaluating user-written code, read `.agents/rubrics/engineering_review.md` and apply it.
- Before creating or updating task files, read `.agents/schemas/task.schema.yaml`.
- Before creating or updating progress files, read `.agents/schemas/progress.schema.yaml`.
- You own workflow logging: create or update `.rv/tasks/` when assigning work, and `.rv/progress/` after review.
- Do not ask the user to maintain task or progress logs. Ask only for missing facts or evidence you cannot inspect yourself, then record that information yourself.
- After a task is reviewed, log what you asked the user to do, what the user did, reviewed evidence, acceptance status, and remaining gaps in `.rv/progress/`.
"""


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
    setup_terminal_launched: bool
    bug_seeds: tuple[AppliedBugSeed, ...]


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
        bug_seeds=bug_seeds,
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
    """Open a terminal that installs backend and frontend dependencies."""

    if os.name != "nt":
        return False

    project_dir = str(target.resolve())
    command = render_setup_terminal_command(Path(project_dir))

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


def render_setup_terminal_command(target: Path) -> str:
    escaped_project_dir = str(target.resolve()).replace("'", "''")
    return (
        f"Set-Location -LiteralPath '{escaped_project_dir}'; "
        "Write-Host '[setup] Creating venv'; "
        "python -m venv venv; "
        "Write-Host '[setup] Activating venv'; "
        ". .\\venv\\Scripts\\Activate.ps1; "
        "if (Test-Path requirements.txt) { "
        "Write-Host '[setup] Installing Python requirements into active venv'; "
        "python -m pip install -r requirements.txt; "
        "} "
        "if (Test-Path mobile\\package.json) { "
        "Write-Host '[setup] Installing frontend packages'; "
        "Push-Location mobile; npm install; Pop-Location; "
        "} "
        "Write-Host '[setup] Ready. Python venv is active in this terminal and frontend packages are installed when package.json exists.'"
    )


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
    agent_context = render_agent_context(options, backend, frontend, compose_result, file_map)
    file_map_content = render_file_map(file_map)
    task_content = task_path.read_text(encoding="utf-8")
    mentor_prompt = read_mentor_prompt(options.mentor_prompt_path)
    mentor_guardrails = read_mentor_guardrails(options.mentor_guardrails_path)
    files = {
        "agent_context.md": agent_context,
        "file_map.md": file_map_content,
        "agent_handoff.md": render_agent_handoff(
            options=options,
            mentor_prompt=mentor_prompt,
            mentor_guardrails=mentor_guardrails,
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
    written.extend(write_native_instruction_files(target, mentor_prompt, mentor_guardrails))
    written.extend(task_files)
    written.extend(progress_files)
    return tuple(written)


def read_mentor_prompt(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return """# Reverse VibeCoding Operator Prompt

You are the operator/reviewer in a reverse-vibecoding workflow. The user implements all code changes. Ask the user for implementation, collect evidence from files/diffs/commands when possible, and review the result. You own `.rv/tasks/` and `.rv/progress/` logging. Do not edit project files yourself.
""".strip()


def read_mentor_guardrails(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return DEFAULT_MENTOR_GUARDRAILS.strip()


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
    ignored_parts = {"venv", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
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

Use this file as project context only. Generic operator behavior lives in `.agents/global_prompt.md`, and per-response guardrails live in `.agents/global_guardrails.md`.
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


def render_initial_task(options: InitProjectOptions) -> str:
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
  - "Confirm the setup terminal completed successfully or run backend and frontend setup manually."
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
1. Confirm the setup terminal completed successfully or run backend and frontend setup manually.
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
    options: InitProjectOptions,
    mentor_prompt: str,
    mentor_guardrails: str,
    agent_context: str,
    task_content: str,
    file_map_content: str,
) -> str:
    return f"""# Agent Handoff

Read this file first and begin the reverse-vibecoding workflow immediately.

Your first response should:

1. Read `.agents/global_guardrails.md` and apply it before every response.
2. Acknowledge the project context briefly.
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

Project path: sandbox/{options.name}
"""


def render_agent_handoff_short(options: InitProjectOptions) -> str:
    return f"""# Short Agent Handoff

Paste this into your IDE agent when context is limited.

You are the operator/reviewer in a reverse-vibecoding workflow. The user implements all code changes. Do not edit project files or solve the project yourself; ask the user to implement.

Project: {options.name}
Domain: {options.domain}
Backend: {options.backend_stack} {options.backend_level}
Frontend: {options.frontend_stack} {options.frontend_level}
Database: {options.database}

Current task: understand and verify the generated app. Start by inspecting `.rv/tasks/`, `.rv/progress/`, source files, diffs, and any user-provided context before asking for missing information.

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
