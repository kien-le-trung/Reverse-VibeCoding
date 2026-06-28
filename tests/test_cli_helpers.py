import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class CliHelperTests(unittest.TestCase):
    def test_init_project_generates_fullstack_project_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            self.assertTrue((result.target / "backend/app/main.py").exists())
            self.assertTrue((result.target / "mobile/App.tsx").exists())
            self.assertTrue((result.target / ".rv/project.json").exists())
            self.assertTrue((result.target / ".rv/frontend_dependencies.json").exists())
            self.assertFalse((result.target / ".rv/mentor_guardrails.md").exists())
            self.assertTrue((result.target / ".rv/agent_context.md").exists())
            self.assertTrue((result.target / ".rv/tasks/README.md").exists())
            self.assertTrue((result.target / ".rv/tasks/001_understand_repo.md").exists())
            self.assertTrue((result.target / ".rv/progress/README.md").exists())
            self.assertTrue((result.target / ".rv/file_map.md").exists())
            self.assertTrue((result.target / ".rv/agent_handoff.md").exists())
            self.assertTrue((result.target / ".rv/agent_handoff_short.md").exists())
            self.assertTrue((result.target / "requirements.txt").exists())
            self.assertIn("react_native_fastapi", result.compose_result.applied_layers)
            self.assertIn("fastapi>=0.115", (result.target / "requirements.txt").read_text())
            self.assertIn("Project: sample", (result.target / ".rv/agent_context.md").read_text())
            self.assertIn("Reverse Vibe Coding Mentor Prompt", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("apply it before every response", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/mentor_guardrails.md", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/rubrics/engineering_review.md", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/schemas/task.schema.yaml", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/schemas/progress.schema.yaml", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("Task 001", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("Paste this into your IDE agent", (result.target / ".rv/agent_handoff_short.md").read_text())
            self.assertIn("Task 001", (result.target / ".rv/tasks/001_understand_repo.md").read_text())
            self.assertIn("Learning Progress", (result.target / ".rv/progress/README.md").read_text())
            self.assertFalse(result.setup_terminal_launched)

    def test_init_project_rejects_existing_target_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample"
            target.mkdir()

            with self.assertRaises(FileExistsError):
                init_project(
                    InitProjectOptions(
                        name="sample",
                        templates_root=TEMPLATES,
                        sandbox_root=Path(tmp),
                        setup_environment=False,
                    )
                )

    def test_init_project_records_selected_stacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    backend_stack="fastapi",
                    frontend_stack="react_native",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            metadata = (result.target / ".rv/project.json").read_text(encoding="utf-8")

            self.assertIn('"stack": "fastapi"', metadata)
            self.assertIn('"stack": "react_native"', metadata)

    def test_init_project_supports_additional_stack_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    backend_stack="nodejs",
                    frontend_stack="vue",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            self.assertTrue((result.target / "backend/src/main.js").exists())
            self.assertTrue((result.target / "mobile/src/main.ts").exists())
            self.assertIn("nodejs_base", result.compose_result.applied_layers)
            self.assertIn("vue_base", result.compose_result.applied_layers)
            self.assertIn("vue_nodejs", result.compose_result.applied_layers)

    def test_init_project_reports_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            messages: list[str] = []

            init_project(
                InitProjectOptions(
                    name="sample",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                ),
                progress=messages.append,
            )

            self.assertIn("[init:check]", messages[0])
            self.assertTrue(any(message.startswith("[init:compose]") for message in messages))
            self.assertTrue(any(message.startswith("[init:agent]") for message in messages))
            self.assertTrue(any(message.startswith("[init:setup] Skipping") for message in messages))


if __name__ == "__main__":
    unittest.main()
