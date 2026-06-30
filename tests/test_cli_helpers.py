import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.cli.helpers import (
    DoctorOptions,
    ImportProjectOptions,
    InitProjectOptions,
    NO_DATABASE,
    NO_DOMAIN,
    doctor,
    import_project,
    init_project,
    resolve_project_target,
    render_dependency_setup_command,
    selected_database_overlays,
    selected_domain_overlays,
)

try:
    from typer.testing import CliRunner

    from reverse_vibecoding.cli.app import app
except ModuleNotFoundError:
    CliRunner = None
    app = None


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
RUNNER = CliRunner() if CliRunner is not None else None


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
            self.assertFalse(result.project_opened)
            self.assertFalse(result.setup_process_launched)

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

    def test_init_project_supports_no_database_for_level_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    backend_level="level_2",
                    frontend_level="level_2",
                    database=NO_DATABASE,
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            metadata = (result.target / ".rv/project.json").read_text(encoding="utf-8")

            self.assertIn('"database": "no_database"', metadata)
            self.assertNotIn('"sqlite"', metadata)
            self.assertNotIn("sqlite", result.backend.manifest_ids)

    def test_no_database_selects_no_database_overlay(self) -> None:
        self.assertEqual((), selected_database_overlays(NO_DATABASE))
        self.assertEqual(("sqlite",), selected_database_overlays("sqlite"))

    def test_init_project_supports_no_domain_and_no_database_for_level_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    backend_level="level_1",
                    frontend_level="level_1",
                    domain=NO_DOMAIN,
                    database=NO_DATABASE,
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            metadata = (result.target / ".rv/project.json").read_text(encoding="utf-8")

            self.assertIn('"domain": "no_domain"', metadata)
            self.assertIn('"database": "no_database"', metadata)
            self.assertNotIn("todo_app", result.backend.manifest_ids)
            self.assertNotIn("todo_app", result.frontend.manifest_ids)
            self.assertNotIn("sqlite", result.backend.manifest_ids)

    def test_no_domain_selects_no_domain_overlay(self) -> None:
        self.assertEqual((), selected_domain_overlays(NO_DOMAIN))
        self.assertEqual(("todo_app",), selected_domain_overlays("todo_app"))

    def test_init_project_reports_conflicting_level_and_domain_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Conflicting init options: .*--domain todo_app"):
                init_project(
                    InitProjectOptions(
                        name="sample",
                        backend_level="level_1",
                        frontend_level="level_1",
                        database=NO_DATABASE,
                        templates_root=TEMPLATES,
                        sandbox_root=Path(tmp),
                        setup_environment=False,
                    )
                )

    def test_init_project_reports_conflicting_level_and_database_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Conflicting init options: .*--database sqlite"):
                init_project(
                    InitProjectOptions(
                        name="sample",
                        backend_level="level_2",
                        frontend_level="level_2",
                        templates_root=TEMPLATES,
                        sandbox_root=Path(tmp),
                        setup_environment=False,
                    )
                )

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

    def test_setup_command_installs_generated_project_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = render_dependency_setup_command(Path(tmp))

            activate_index = command.index(". .\\venv\\Scripts\\Activate.ps1")
            pip_index = command.index("python -m pip install -r requirements.txt")

            self.assertLess(activate_index, pip_index)
            self.assertIn("Installing Python requirements into active venv", command)
            self.assertIn("Push-Location backend; npm install; Pop-Location", command)
            self.assertIn("mvn dependency:go-offline", command)
            self.assertIn("Push-Location mobile; npm install; Pop-Location", command)

    def test_import_project_writes_agent_mechanism_into_existing_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing_project"
            target.mkdir()
            (target / "README.md").write_text("# Existing Project\n", encoding="utf-8")

            result = import_project(
                ImportProjectOptions(
                    target=target.resolve(),
                    agents_root=ROOT / ".agents",
                    mentor_prompt_path=ROOT / ".agents" / "global_prompt.md",
                    mentor_guardrails_path=ROOT / ".agents" / "global_guardrails.md",
                )
            )

            self.assertEqual(target.resolve(), result.target)
            self.assertTrue((target / ".agents/global_prompt.md").exists())
            self.assertTrue((target / ".agents/rubrics/engineering_review.md").exists())
            self.assertTrue((target / ".agents/schemas/task.schema.yaml").exists())
            self.assertTrue((target / ".rv/project.json").exists())
            self.assertTrue((target / ".rv/agent_context.md").exists())
            self.assertTrue((target / ".rv/file_map.md").exists())
            self.assertTrue((target / ".rv/tasks/001_understand_repo.md").exists())
            self.assertTrue((target / ".rv/progress/README.md").exists())
            self.assertTrue((target / ".rv/agent_handoff.md").exists())
            self.assertTrue((target / ".rv/agent_handoff_short.md").exists())
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertTrue((target / "CLAUDE.md").exists())
            self.assertTrue((target / ".github/copilot-instructions.md").exists())
            self.assertTrue((target / ".github/instructions/reverse-vibecoding.instructions.md").exists())
            self.assertIn('"mode": "imported"', (target / ".rv/project.json").read_text(encoding="utf-8"))
            self.assertIn("Mode: imported existing project", (target / ".rv/agent_context.md").read_text(encoding="utf-8"))
            self.assertIn("README.md", (target / ".rv/file_map.md").read_text(encoding="utf-8"))
            self.assertNotIn(".agents/global_prompt.md", (target / ".rv/file_map.md").read_text(encoding="utf-8"))

    def test_import_project_requires_absolute_existing_directory(self) -> None:
        with self.assertRaises(ValueError):
            import_project(ImportProjectOptions(target=Path("relative/project"), agents_root=ROOT / ".agents"))

    def test_doctor_reports_required_and_optional_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / ".agents"
            (agents / "schemas").mkdir(parents=True)
            (agents / "rubrics").mkdir()
            (agents / "global_prompt.md").write_text("prompt", encoding="utf-8")
            (agents / "global_guardrails.md").write_text("guardrails", encoding="utf-8")
            (agents / "schemas/task.schema.yaml").write_text("task", encoding="utf-8")
            (agents / "schemas/progress.schema.yaml").write_text("progress", encoding="utf-8")
            (agents / "rubrics/engineering_review.md").write_text("rubric", encoding="utf-8")
            templates = root / "templates"
            templates.mkdir()
            sandbox = root / "sandbox"
            sandbox.mkdir()

            result = doctor(
                DoctorOptions(agents_root=agents, templates_root=templates, sandbox_root=sandbox),
                command_resolver=lambda command: "C:/bin/" + command if command in {"code", "node", "npm"} else None,
                python_version=(3, 11, 0),
            )

            self.assertTrue(result.ok)
            checks = {check.name: check for check in result.checks}
            self.assertTrue(checks["python"].ok)
            self.assertTrue(checks["agents"].ok)
            self.assertTrue(checks["templates"].ok)
            self.assertTrue(checks["sandbox"].ok)
            self.assertTrue(checks["code"].ok)
            self.assertFalse(checks["mvn"].ok)
            self.assertFalse(checks["mvn"].required)

    def test_doctor_fails_when_required_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = doctor(
                DoctorOptions(
                    agents_root=Path(tmp) / "missing_agents",
                    templates_root=Path(tmp) / "missing_templates",
                    sandbox_root=Path(tmp) / "missing_sandbox",
                ),
                command_resolver=lambda _command: None,
                python_version=(3, 10, 0),
            )

            self.assertFalse(result.ok)
            self.assertFalse(next(check for check in result.checks if check.name == "python").ok)
            self.assertFalse(next(check for check in result.checks if check.name == "agents").ok)

    def test_resolve_project_target_accepts_sandbox_name_or_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            target = sandbox / "sample"
            target.mkdir(parents=True)

            self.assertEqual(target.resolve(), resolve_project_target(Path("sample"), sandbox_root=sandbox))
            self.assertEqual(target.resolve(), resolve_project_target(target, sandbox_root=sandbox))

    def test_init_help_lists_available_option_values(self) -> None:
        if RUNNER is None or app is None:
            self.skipTest("typer is not installed")

        result = RUNNER.invoke(app, ["init", "--help"])

        self.assertEqual(0, result.exit_code)
        for value in (
            "fastapi",
            "nodejs",
            "flask",
            "django",
            "spring_boot",
            "react_native",
            "vue",
            "react",
            "angular",
            "no_domain",
            "todo_app",
            "habit_tracker",
            "expense_tracker",
            "no_database",
            "sqlite",
            "postgresql_local",
            "postgresql_supabase",
            "level_1",
            "level_2",
            "level_3",
            "level_4",
            "api_integration",
            "boundary_status_code",
            "environment_config",
            "http_status",
            "partial_update",
            "response_shape",
            "route_mismatch",
            "validation",
        ):
            self.assertIn(value, result.output)


if __name__ == "__main__":
    unittest.main()
