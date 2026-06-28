"""Project specification generation without any CLI concerns."""

from __future__ import annotations

import random
from collections.abc import Sequence

from reverse_vibecoding.catalog import COMPLETENESS_LEVELS, DOMAINS, SCENARIOS, STACKS, TASKS
from reverse_vibecoding.models import CompletenessLevel, Domain, ProjectSpec, Scenario, Stack, Task


class ProjectCatalog:
    """Read-only facade over built-in generation options."""

    def __init__(
        self,
        domains: Sequence[Domain] = DOMAINS,
        stacks: Sequence[Stack] = STACKS,
        completeness_levels: Sequence[CompletenessLevel] = COMPLETENESS_LEVELS,
        scenarios: dict[str, Scenario] = SCENARIOS,
        tasks: dict[str, Task] = TASKS,
    ) -> None:
        self.domains = tuple(domains)
        self.stacks = tuple(stacks)
        self.completeness_levels = tuple(completeness_levels)
        self.scenarios = dict(scenarios)
        self.tasks = dict(tasks)


class ProjectSpecGenerator:
    """Generate randomized project specs from orthogonal components."""

    def __init__(self, catalog: ProjectCatalog | None = None) -> None:
        self.catalog = catalog or ProjectCatalog()

    def generate(
        self,
        *,
        seed: int | None = None,
        domain: Domain | None = None,
        stack: Stack | None = None,
        completeness: CompletenessLevel | None = None,
        scenario_count: int = 1,
    ) -> ProjectSpec:
        rng = random.Random(seed)

        selected_domain = domain or rng.choice(self.catalog.domains)
        selected_stack = stack or rng.choice(self.catalog.stacks)
        selected_completeness = completeness or rng.choice(self.catalog.completeness_levels)

        scenario_ids = self._sample_scenarios(rng, scenario_count)
        task_ids = self._derive_task_sequence(scenario_ids)

        return ProjectSpec(
            domain=selected_domain,
            stack=selected_stack,
            completeness=selected_completeness,
            scenario_ids=scenario_ids,
            task_ids=task_ids,
            seed=seed,
        )

    def _sample_scenarios(self, rng: random.Random, scenario_count: int) -> tuple[str, ...]:
        if scenario_count < 0:
            raise ValueError("scenario_count must be non-negative")
        scenario_ids = tuple(self.catalog.scenarios)
        count = min(scenario_count, len(scenario_ids))
        return tuple(rng.sample(scenario_ids, count))

    def _derive_task_sequence(self, scenario_ids: tuple[str, ...]) -> tuple[str, ...]:
        task_ids: list[str] = ["design_data_model", "implement_crud"]
        for scenario_id in scenario_ids:
            task_ids.extend(self.catalog.scenarios[scenario_id].task_ids)
        task_ids.append("review_and_refactor")
        return tuple(dict.fromkeys(task_ids))

