"""Render generated specs into local project metadata and mentor prompts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from reverse_vibecoding.catalog import SCENARIOS, TASKS
from reverse_vibecoding.models import ProjectSpec


def render_project_metadata(spec: ProjectSpec) -> str:
    """Return stable JSON metadata suitable for a future `.rv/project.json` file."""

    return json.dumps(asdict(spec), indent=2, sort_keys=True)


def render_mentor_prompt(spec: ProjectSpec) -> str:
    """Create a mentor prompt students can paste into their preferred AI tool."""

    scenario_titles = ", ".join(SCENARIOS[id].title for id in spec.scenario_ids) or "None"
    task_lines = "\n".join(f"- {TASKS[id].title}: {TASKS[id].learner_goal}" for id in spec.task_ids)

    return (
        "You are the AI mentor for a Reverse Vibe Coding project.\n"
        "Do not edit project files or write production code for the student.\n"
        "Ask architectural questions, request evidence when useful, and review decisions critically.\n"
        "If the student explicitly asks for an example, provide a small illustrative snippet in chat.\n\n"
        f"Domain: {spec.domain.value}\n"
        f"Backend: {spec.stack.backend.value}\n"
        f"Frontend: {spec.stack.frontend.value}\n"
        f"Database: {spec.stack.database.value}\n"
        f"Completeness: {spec.completeness.value}\n"
        f"Scenarios: {scenario_titles}\n\n"
        "Task sequence:\n"
        f"{task_lines}\n"
    )


def write_generated_frame(spec: ProjectSpec, target_dir: Path) -> None:
    """Write only framework metadata and prompts for a generated project."""

    rv_dir = target_dir / ".rv"
    prompt_dir = target_dir / "prompts"
    rv_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    (rv_dir / "project.json").write_text(render_project_metadata(spec), encoding="utf-8")
    (prompt_dir / "mentor.md").write_text(render_mentor_prompt(spec), encoding="utf-8")
