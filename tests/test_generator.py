import unittest

from reverse_vibecoding.generator import ProjectSpecGenerator
from reverse_vibecoding.models import Backend, CompletenessLevel, Database, Domain, Frontend, Stack
from reverse_vibecoding.rendering import render_mentor_prompt, render_project_metadata


class ProjectSpecGeneratorTests(unittest.TestCase):
    def test_generator_is_deterministic_for_seed(self) -> None:
        generator = ProjectSpecGenerator()

        first = generator.generate(seed=42)
        second = generator.generate(seed=42)

        self.assertEqual(first, second)

    def test_generator_accepts_explicit_components(self) -> None:
        stack = Stack(Backend.FASTAPI, Frontend.BACKEND_ONLY, Database.SQLITE)
        spec = ProjectSpecGenerator().generate(
            seed=7,
            domain=Domain.TODO_APP,
            stack=stack,
            completeness=CompletenessLevel.MINIMAL,
            scenario_count=0,
        )

        self.assertIs(spec.domain, Domain.TODO_APP)
        self.assertEqual(spec.stack, stack)
        self.assertIs(spec.completeness, CompletenessLevel.MINIMAL)
        self.assertEqual(spec.scenario_ids, ())
        self.assertEqual(spec.task_ids, ("design_data_model", "implement_crud", "review_and_refactor"))

    def test_renderers_include_core_project_context(self) -> None:
        spec = ProjectSpecGenerator().generate(seed=1)

        metadata = render_project_metadata(spec)
        prompt = render_mentor_prompt(spec)

        self.assertIn(spec.domain.value, metadata)
        self.assertIn(spec.stack.backend.value, prompt)
        self.assertIn("The other participant is the coding agent and must implement code changes.", prompt)
        self.assertIn("Do not edit project files or write production code yourself.", prompt)


if __name__ == "__main__":
    unittest.main()
