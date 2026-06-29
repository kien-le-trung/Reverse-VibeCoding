import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project, render_setup_terminal_command


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
            self.assertFalse((result.target / ".rv/global_guardrails.md").exists())
            self.assertTrue((result.target / ".rv/agent_context.md").exists())
            self.assertTrue((result.target / ".rv/tasks/README.md").exists())
            self.assertTrue((result.target / ".rv/tasks/001_understand_repo.md").exists())
            self.assertTrue((result.target / ".rv/progress/README.md").exists())
            self.assertTrue((result.target / ".rv/file_map.md").exists())
            self.assertTrue((result.target / ".rv/agent_handoff.md").exists())
            self.assertTrue((result.target / ".rv/agent_handoff_short.md").exists())
            self.assertTrue((result.target / "AGENTS.md").exists())
            self.assertTrue((result.target / "CLAUDE.md").exists())
            self.assertTrue((result.target / ".github/copilot-instructions.md").exists())
            self.assertTrue((result.target / ".github/instructions/reverse-vibecoding.instructions.md").exists())
            self.assertTrue((result.target / "requirements.txt").exists())
            self.assertIn("react_native_fastapi", result.compose_result.applied_layers)
            self.assertIn("fastapi>=0.115", (result.target / "requirements.txt").read_text())
            self.assertIn("Project: sample", (result.target / ".rv/agent_context.md").read_text())
            self.assertIn("Reverse VibeCoding Operator Prompt", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("The user implements all code changes.", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("The user implements all code changes.", (result.target / "AGENTS.md").read_text())
            self.assertIn("The user implements all code changes.", (result.target / "CLAUDE.md").read_text())
            self.assertIn("The user implements all code changes.", (result.target / ".github/copilot-instructions.md").read_text())
            self.assertIn("apply it before every response", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/global_guardrails.md", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/rubrics/engineering_review.md", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/schemas/task.schema.yaml", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn(".agents/schemas/progress.schema.yaml", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("Task 001", (result.target / ".rv/agent_handoff.md").read_text())
            self.assertIn("Paste this into your IDE agent", (result.target / ".rv/agent_handoff_short.md").read_text())
            self.assertIn("Task 001", (result.target / ".rv/tasks/001_understand_repo.md").read_text())
            self.assertIn("Reverse VibeCoding Progress", (result.target / ".rv/progress/README.md").read_text())
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

            metadata = (result.target / ".rv/project.json").read_text(encoding="utf-8")

            self.assertIn('"express@^4.19.2"', metadata)
            self.assertIn('"vue@^3.4.0"', metadata)

    def test_init_project_records_maven_dependencies_for_spring_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    backend_stack="spring_boot",
                    frontend_stack="react",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            metadata = (result.target / ".rv/project.json").read_text(encoding="utf-8")

            self.assertIn('"maven_dependencies"', metadata)
            self.assertIn('"org.springframework.boot:spring-boot-starter-web:3.3.0"', metadata)

    def test_init_project_writes_requirements_for_python_backends(self) -> None:
        for backend_stack, expected_dependency in (
            ("django", "django>=5.0"),
            ("flask", "flask>=3.0"),
            ("fastapi", "fastapi>=0.115"),
        ):
            with self.subTest(backend_stack=backend_stack):
                with tempfile.TemporaryDirectory() as tmp:
                    result = init_project(
                        InitProjectOptions(
                            name="sample",
                            backend_stack=backend_stack,
                            frontend_stack="react",
                            templates_root=TEMPLATES,
                            sandbox_root=Path(tmp),
                            setup_environment=False,
                        )
                    )

                    requirements = result.target / "requirements.txt"

                    self.assertTrue(requirements.exists())
                    self.assertIn(expected_dependency, requirements.read_text(encoding="utf-8"))

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

    def test_setup_terminal_command_activates_venv_before_installing_python_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = render_setup_terminal_command(Path(tmp))

            activate_index = command.index(". .\\venv\\Scripts\\Activate.ps1")
            pip_index = command.index("python -m pip install -r requirements.txt")

            self.assertLess(activate_index, pip_index)
            self.assertIn("Installing Python requirements into active venv", command)
            self.assertIn("Push-Location mobile; npm install; Pop-Location", command)


if __name__ == "__main__":
    unittest.main()
