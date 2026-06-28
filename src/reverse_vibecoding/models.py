"""Shared data models for generated apprenticeship projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Domain(StrEnum):
    TODO_APP = "todo_app"
    HABIT_TRACKER = "habit_tracker"
    EXPENSE_TRACKER = "expense_tracker"


class Backend(StrEnum):
    FASTAPI = "fastapi"


class Frontend(StrEnum):
    REACT_NATIVE = "react_native"
    BACKEND_ONLY = "backend_only"


class Database(StrEnum):
    SQLITE = "sqlite"
    POSTGRESQL_LOCAL = "postgresql_local"
    POSTGRESQL_SUPABASE = "postgresql_supabase"


class CompletenessLevel(StrEnum):
    MINIMAL = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"


@dataclass(frozen=True)
class Stack:
    backend: Backend
    frontend: Frontend
    database: Database


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    learner_goal: str
    acceptance_criteria: tuple[str, ...] = ()
    reflection_questions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    task_ids: tuple[str, ...] = ()
    bug_seed_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectSpec:
    domain: Domain
    stack: Stack
    completeness: CompletenessLevel
    scenario_ids: tuple[str, ...] = ()
    task_ids: tuple[str, ...] = ()
    seed: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)
