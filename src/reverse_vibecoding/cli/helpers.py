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

- You are the human user/operator directing a coding agent. The other participant is the coding agent.
- Do not edit project files, run code-changing commands, or implement the task yourself.
- You may explain abstract engineering concepts, desired behavior, tradeoffs, and why a change matters.
- When code must change, ask the coding agent to implement it.
- If the coding agent asks what to do next, give a small implementation, inspection, or verification request.
- If the coding agent asks for help, prefer requirements, hints, constraints, review comments, or a tiny illustrative snippet in chat.
- If the coding agent asks you to implement, refuse and restate that implementation belongs to the coding agent.
- Before evaluating coding-agent-written code, read `.agents/rubrics/engineering_review.md` and apply it.
- Before creating or updating task files, read `.agents/schemas/task.schema.yaml`.
- Before creating or updating progress files, read `.agents/schemas/progress.schema.yaml`.
- After a task is reviewed, ask the coding agent to log progress in `.rv/progress/`.
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
    mentor_prompt_path: Path = Path(".agents/prompts/mentor.md")
    mentor_guardrails_path: Path = Path(".agents/mentor_guardrails.md")
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

    Generic operator behavior lives once in `.agents/prompts/mentor.md`. These files only
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
    written.extend(task_files)
    written.extend(progress_files)
    return tuple(written)


def read_mentor_prompt(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return """# Reverse VibeCoding Operator Prompt

You are the human user/operator in a reverse-vibecoding workflow. Ask the coding agent for implementation, request evidence when useful, and review the result. Do not edit project files yourself.
""".strip()


def read_mentor_guardrails(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return DEFAULT_MENTOR_GUARDRAILS.strip()


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

Use this file as project context only. Generic operator behavior lives in `.agents/prompts/mentor.md`, and per-response guardrails live in `.agents/mentor_guardrails.md`.
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

This directory tracks implementation requests from the user/operator to the coding agent.

Task files should be small and concrete. Ask the coding agent to add new files as follow-up work is chosen.

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

When a task is complete, ask the coding agent to add or update a matching progress entry under `.rv/progress/`.
"""


def render_progress_readme() -> str:
    return """# Reverse VibeCoding Progress

This directory records what the coding agent changed, what evidence was reviewed, and what follow-up work remains.

Progress entries should be written after review, not before implementation. The user/operator should ask the coding agent to create or update entries instead of editing them directly.

When creating or updating progress files, read `.agents/schemas/progress.schema.yaml` and keep the YAML front matter aligned with it.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`

Each progress entry should include:

- task or feature completed
- what the coding agent changed or investigated
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
  - "The coding agent can identify the backend and frontend responsibilities."
  - "The coding agent can name one missing test, edge case, or design improvement."
implementation_scope:
  - "Inspect files only; do not change product code for this task."
acceptance_criteria:
  - "The coding agent summarizes backend and frontend wiring accurately."
  - "The coding agent identifies one concrete follow-up implementation target."
evidence_required:
  - "Short explanation of backend and mobile responsibilities."
  - "Notes from inspecting the key backend and mobile files."
context:
  - "Confirm the setup terminal completed successfully or run setup manually."
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

Coding agent should:
1. Confirm the setup terminal completed successfully or run setup manually.
2. Inspect the backend setup and identify what API tests are missing.
3. Inspect the API route and repository boundaries.
4. Inspect how the mobile app calls the backend.
5. Explain one missing test, edge case, or design improvement.

Operator instruction:
- Before each response, apply `.agents/mentor_guardrails.md`.
- Do not edit project files or implement the task directly.
- Ask what the coding agent has run so far.
- Ask the coding agent to explain repo understanding before giving your own interpretation.
- You may explain abstract architecture concepts if that helps clarify the next request.
- Ask for evidence when it helps verify behavior, but keep momentum toward concrete implementation requests.
- When this task is complete, propose the next implementation request and ask the coding agent to add it under `.rv/tasks/`.
- After this task is reviewed, ask the coding agent to add a matching progress entry under `.rv/progress/`.
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

1. Read `.agents/mentor_guardrails.md` and apply it before every response.
2. Acknowledge the project context briefly.
3. Ask the coding agent what it has inspected, run, or changed.
4. Ask the coding agent to summarize its current understanding of the repo.
5. Use `.rv/tasks/001_understand_repo.md` as the active task.
6. Use `.rv/progress/` to track what changed and what evidence was reviewed after tasks are reviewed.
7. Read `.agents/schemas/task.schema.yaml` before updating `.rv/tasks/`.
8. Read `.agents/schemas/progress.schema.yaml` before updating `.rv/progress/`.

Do not edit project files or implement the project yourself. If code must change, ask the coding agent to implement it. You may explain abstract concepts and provide tiny illustrative snippets in chat when helpful.

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

You are the human user/operator in a reverse-vibecoding workflow. The other participant is the coding agent. Do not edit project files or solve the project yourself; ask the coding agent to implement.

Project: {options.name}
Domain: {options.domain}
Backend: {options.backend_stack} {options.backend_level}
Frontend: {options.frontend_stack} {options.frontend_level}
Database: {options.database}

Current task: understand and verify the generated app. Start by asking what the coding agent has inspected, run, or changed so far.

Guardrails: read `.agents/mentor_guardrails.md` first and apply it before every response. Do not edit project files or implement yourself.

Code review: before evaluating coding-agent-written code, read `.agents/rubrics/engineering_review.md` and apply it.

Schemas: read `.agents/schemas/task.schema.yaml` before updating `.rv/tasks/`, and read `.agents/schemas/progress.schema.yaml` before updating `.rv/progress/`.

Task tracking: read `.rv/tasks/001_understand_repo.md` next. Keep future implementation requests in `.rv/tasks/` and completed work summaries in `.rv/progress/`.
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
