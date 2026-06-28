"""Built-in catalog entries used by generators and assessments."""

from __future__ import annotations

from reverse_vibecoding.models import (
    Backend,
    CompletenessLevel,
    Database,
    Domain,
    Frontend,
    Scenario,
    Stack,
    Task,
)

DOMAINS: tuple[Domain, ...] = (
    Domain.TODO_APP,
    Domain.HABIT_TRACKER,
    Domain.EXPENSE_TRACKER,
)

STACKS: tuple[Stack, ...] = (
    Stack(Backend.FASTAPI, Frontend.BACKEND_ONLY, Database.SQLITE),
    Stack(Backend.FASTAPI, Frontend.REACT_NATIVE, Database.SQLITE),
    Stack(Backend.FASTAPI, Frontend.REACT_NATIVE, Database.POSTGRESQL_LOCAL),
    Stack(Backend.FASTAPI, Frontend.REACT_NATIVE, Database.POSTGRESQL_SUPABASE),
)

COMPLETENESS_LEVELS: tuple[CompletenessLevel, ...] = tuple(CompletenessLevel)

TASKS: dict[str, Task] = {
    "design_data_model": Task(
        id="design_data_model",
        title="Design the data model",
        learner_goal="Define entities, relationships, constraints, and edge cases before coding.",
        acceptance_criteria=(
            "Data model captures the selected domain requirements.",
            "Validation and persistence constraints are documented.",
        ),
        reflection_questions=(
            "Which invariant matters most for this domain?",
            "What tradeoff did you make between simplicity and future flexibility?",
        ),
    ),
    "implement_crud": Task(
        id="implement_crud",
        title="Implement core CRUD behavior",
        learner_goal="Build the smallest useful vertical slice with tests.",
        acceptance_criteria=(
            "Create, read, update, and delete paths work for the core entity.",
            "Unit or integration tests cover success and failure paths.",
        ),
        reflection_questions=(
            "Where did validation belong in your design?",
            "What failure mode did your tests catch?",
        ),
    ),
    "review_and_refactor": Task(
        id="review_and_refactor",
        title="Review and refactor",
        learner_goal="Improve maintainability without changing behavior.",
        acceptance_criteria=(
            "Refactor is explained and scoped.",
            "Existing tests still pass after the change.",
        ),
        reflection_questions=(
            "What code smell did you address?",
            "How did you prove behavior stayed the same?",
        ),
    ),
}

SCENARIOS: dict[str, Scenario] = {
    "pagination": Scenario(
        id="pagination",
        title="Pagination",
        description="Large lists require paginated reads with deterministic ordering.",
        task_ids=("implement_crud",),
        bug_seed_ids=("off_by_one_pagination",),
    ),
    "authentication": Scenario(
        id="authentication",
        title="Authentication",
        description="Protected resources require a user identity and authorization checks.",
        task_ids=("design_data_model", "implement_crud"),
        bug_seed_ids=("missing_authorization_check",),
    ),
    "accessibility": Scenario(
        id="accessibility",
        title="Accessibility",
        description="User-facing flows must support keyboard and screen-reader usage.",
        task_ids=("review_and_refactor",),
        bug_seed_ids=("missing_accessible_name",),
    ),
}
