import json
import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.bug_seeds import BUG_SEEDS, BugSeed, apply_random_bug_seeds
from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project

try:
    from typer.testing import CliRunner

    from reverse_vibecoding.cli.app import app
except ModuleNotFoundError:
    CliRunner = None
    app = None


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
BACKEND_STACKS = {"fastapi", "nodejs", "flask", "django", "spring_boot"}
FRONTEND_STACKS = {"react_native", "vue", "react", "angular"}


class BugSeedTests(unittest.TestCase):
    def test_bug_seed_registry_entries_are_complete_and_unique(self) -> None:
        ids = [bug.id for bug in BUG_SEEDS]

        self.assertEqual(len(ids), len(set(ids)))
        for bug in BUG_SEEDS:
            with self.subTest(bug=bug.id):
                self.assertTrue(bug.id)
                self.assertTrue(bug.category)
                self.assertTrue(bug.stacks)
                self.assertTrue(bug.relative_path)
                self.assertTrue(bug.old)
                self.assertNotEqual(bug.old, bug.new)
                self.assertTrue(bug.learning_goal)
                self.assertTrue(bug.description)

    def test_every_bug_seed_matches_a_generated_compatible_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, bug in enumerate(BUG_SEEDS, start=1):
                with self.subTest(bug=bug.id):
                    backend_stack, frontend_stack = _compatible_stacks_for_bug(bug)
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack=frontend_stack,
                    )
                    target_file = result.target / bug.relative_path

                    self.assertTrue(target_file.exists())
                    self.assertIn(bug.old, target_file.read_text(encoding="utf-8"))

    def test_init_project_defaults_to_clean_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(Path(tmp), name="bug_test_01")

            schema = (result.target / "backend/app/schemas/todo.py").read_text(encoding="utf-8")
            project_metadata = _read_json(result.target / ".rv/project.json")
            hidden_manifest = _read_json(result.target / ".rv/hidden_manifest.json")

            self.assertEqual(result.bug_seeds, ())
            self.assertIn("min_length=1", schema)
            self.assertEqual(project_metadata["bug_seed_count"], 0)
            self.assertFalse(project_metadata["bug_hidden"])
            self.assertEqual(hidden_manifest["bug_seeds"], [])

    def test_bug_seed_selection_is_deterministic_for_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            first = _init_project(
                sandbox_root,
                name="bug_test_01",
                bug_seed_count=2,
                bug_seed_random_seed=123,
            )
            second = _init_project(
                sandbox_root,
                name="bug_test_02",
                bug_seed_count=2,
                bug_seed_random_seed=123,
            )

            self.assertEqual([bug.id for bug in first.bug_seeds], [bug.id for bug in second.bug_seeds])
            for bug in first.bug_seeds:
                first_content = (first.target / bug.relative_path).read_text(encoding="utf-8")
                second_content = (second.target / bug.relative_path).read_text(encoding="utf-8")
                self.assertEqual(first_content, second_content)

    def test_category_filtering_only_applies_requested_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("validation",),
            )

            self.assertEqual(len(result.bug_seeds), 1)
            self.assertEqual(result.bug_seeds[0].category, "validation")
            self.assertEqual(result.bug_seeds[0].id, "fastapi_missing_title_min_length")

    def test_category_filtering_rejects_categories_with_no_applicable_bugs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "only 0 are applicable"):
                _init_project(
                    Path(tmp),
                    name="bug_test_01",
                    bug_seed_count=1,
                    bug_categories=("does_not_exist",),
                )

    def test_bug_seed_count_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean = _init_project(Path(tmp), name="bug_test_01")

            self.assertEqual(
                apply_random_bug_seeds(
                    target=clean.target,
                    backend_stack="fastapi",
                    frontend_stack="react_native",
                    count=0,
                ),
                (),
            )
            with self.assertRaisesRegex(ValueError, "non-negative"):
                apply_random_bug_seeds(
                    target=clean.target,
                    backend_stack="fastapi",
                    frontend_stack="react_native",
                    count=-1,
                )
            with self.assertRaisesRegex(ValueError, "only .* are applicable"):
                apply_random_bug_seeds(
                    target=clean.target,
                    backend_stack="fastapi",
                    frontend_stack="react_native",
                    count=99,
                )

    def test_backend_stack_applicability_matrix(self) -> None:
        expectations = (
            ("fastapi", "fastapi_missing_update_404"),
            ("nodejs", "nodejs_missing_update_404"),
            ("flask", "flask_missing_update_404"),
            ("django", "django_missing_update_404"),
            ("spring_boot", "spring_boot_missing_update_404"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (backend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(backend_stack=backend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack="react",
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("boundary_status_code",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_validation_bug_exists_for_every_backend_stack(self) -> None:
        expectations = (
            ("fastapi", "fastapi_missing_title_min_length"),
            ("nodejs", "nodejs_missing_title_validation"),
            ("flask", "flask_missing_title_validation"),
            ("django", "django_missing_title_validation"),
            ("spring_boot", "spring_boot_missing_title_validation"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (backend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(backend_stack=backend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack="react",
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("validation",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_http_status_bug_exists_for_every_backend_stack(self) -> None:
        expectations = (
            ("fastapi", "fastapi_create_returns_200"),
            ("nodejs", "nodejs_create_returns_200"),
            ("flask", "flask_create_returns_200"),
            ("django", "django_create_returns_200"),
            ("spring_boot", "spring_boot_create_returns_200"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (backend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(backend_stack=backend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack="react",
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("http_status",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_partial_update_bug_exists_for_every_backend_stack(self) -> None:
        expectations = (
            ("fastapi", "fastapi_update_resets_completed"),
            ("nodejs", "nodejs_update_resets_completed"),
            ("flask", "flask_update_resets_completed"),
            ("django", "django_update_resets_completed"),
            ("spring_boot", "spring_boot_update_resets_completed"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (backend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(backend_stack=backend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack="react",
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("partial_update",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_response_shape_bug_exists_for_every_backend_stack(self) -> None:
        expectations = (
            ("fastapi", "fastapi_list_response_wrapped"),
            ("nodejs", "nodejs_list_response_wrapped"),
            ("flask", "flask_list_response_wrapped"),
            ("django", "django_list_response_wrapped"),
            ("spring_boot", "spring_boot_list_response_wrapped"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (backend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(backend_stack=backend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack=backend_stack,
                        frontend_stack="react",
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("response_shape",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_frontend_stack_applicability_matrix(self) -> None:
        expectations = (
            ("react_native", "frontend_missing_health_error_check"),
            ("vue", "frontend_web_missing_health_error_check"),
            ("react", "frontend_web_missing_health_error_check"),
            ("angular", "frontend_web_missing_health_error_check"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (frontend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(frontend_stack=frontend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack="fastapi",
                        frontend_stack=frontend_stack,
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("api_integration",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_route_mismatch_bug_exists_for_every_frontend_stack(self) -> None:
        expectations = (
            ("react_native", "react_native_wrong_health_endpoint"),
            ("vue", "frontend_web_wrong_health_endpoint"),
            ("react", "frontend_web_wrong_health_endpoint"),
            ("angular", "frontend_web_wrong_health_endpoint"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            for index, (frontend_stack, expected_id) in enumerate(expectations, start=1):
                with self.subTest(frontend_stack=frontend_stack):
                    result = _init_project(
                        sandbox_root,
                        name=_bug_project_name(index),
                        backend_stack="fastapi",
                        frontend_stack=frontend_stack,
                        bug_seed_count=1,
                        bug_seed_random_seed=1,
                        bug_categories=("route_mismatch",),
                    )

                    self.assertEqual([bug.id for bug in result.bug_seeds], [expected_id])
                    _assert_applied_bug(result.target, _bug_by_id(expected_id))

    def test_environment_config_bug_exists_for_react_native(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                backend_stack="fastapi",
                frontend_stack="react_native",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("environment_config",),
            )

            self.assertEqual([bug.id for bug in result.bug_seeds], ["react_native_wrong_api_base_url_env"])
            _assert_applied_bug(result.target, _bug_by_id("react_native_wrong_api_base_url_env"))

    def test_visible_hidden_manifest_includes_bug_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("validation",),
            )

            manifest = _read_json(result.target / ".rv/hidden_manifest.json")
            bug_entry = manifest["bug_seeds"][0]

            self.assertFalse(manifest["bug_hidden"])
            self.assertFalse(bug_entry["hidden"])
            self.assertEqual(bug_entry["id"], "fastapi_missing_title_min_length")
            self.assertEqual(bug_entry["category"], "validation")
            self.assertEqual(bug_entry["file_changed"], "backend/app/schemas/todo.py")
            self.assertIn("learning_goal", bug_entry)
            self.assertIn("description", bug_entry)

    def test_hidden_manifest_hides_bug_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("validation",),
                bug_hidden=True,
            )

            manifest_text = (result.target / ".rv/hidden_manifest.json").read_text(encoding="utf-8")
            manifest = json.loads(manifest_text)
            bug_entry = manifest["bug_seeds"][0]

            self.assertEqual(len(result.bug_seeds), 1)
            self.assertTrue(manifest["bug_hidden"])
            self.assertEqual(bug_entry["id"], "hidden_bug_1")
            self.assertTrue(bug_entry["hidden"])
            self.assertEqual(bug_entry["files_changed"], "hidden")
            self.assertNotIn("fastapi_missing_title_min_length", manifest_text)
            self.assertNotIn("backend/app/schemas/todo.py", manifest_text)
            self.assertNotIn("validation", manifest_text)
            self.assertNotIn("Todo title no longer rejects empty strings.", manifest_text)

    def test_project_metadata_records_bug_count_and_hidden_flag_without_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("validation",),
                bug_hidden=True,
            )

            metadata_text = (result.target / ".rv/project.json").read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)

            self.assertEqual(metadata["bug_seed_count"], 1)
            self.assertTrue(metadata["bug_hidden"])
            self.assertNotIn("fastapi_missing_title_min_length", metadata_text)
            self.assertNotIn("backend/app/schemas/todo.py", metadata_text)

    def test_reapplying_same_bug_seed_is_rejected_after_old_text_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _init_project(
                Path(tmp),
                name="bug_test_01",
                bug_seed_count=1,
                bug_seed_random_seed=1,
                bug_categories=("validation",),
            )

            with self.assertRaisesRegex(ValueError, "only 0 are applicable"):
                apply_random_bug_seeds(
                    target=result.target,
                    backend_stack="fastapi",
                    frontend_stack="react_native",
                    count=1,
                    seed=1,
                    categories=("validation",),
                )

    @unittest.skipUnless(CliRunner is not None and app is not None, "typer is not installed")
    def test_cli_visible_hidden_and_clean_bug_outputs(self) -> None:
        assert CliRunner is not None
        assert app is not None
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp)
            visible = runner.invoke(
                app,
                [
                    "init",
                    "bug_test_01",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--no-setup",
                    "--bug-seed-count",
                    "1",
                    "--bug-seed-random-seed",
                    "1",
                    "--bug-category",
                    "validation",
                ],
            )
            hidden = runner.invoke(
                app,
                [
                    "init",
                    "bug_test_02",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--no-setup",
                    "--bug-seed-count",
                    "1",
                    "--bug-seed-random-seed",
                    "1",
                    "--bug-category",
                    "validation",
                    "--bug-hidden",
                ],
            )
            clean = runner.invoke(
                app,
                [
                    "init",
                    "bug_test_03",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--no-setup",
                    "--bug-seed-count",
                    "1",
                    "--bug-category",
                    "validation",
                    "--no-bugs",
                ],
            )

            self.assertEqual(visible.exit_code, 0, visible.output)
            self.assertIn("Applied bug seeds: 1", visible.output)
            self.assertIn("fastapi_missing_title_min_length (validation)", visible.output)

            self.assertEqual(hidden.exit_code, 0, hidden.output)
            self.assertIn("Applied bug seeds: 1", hidden.output)
            self.assertIn("Details hidden", hidden.output)
            self.assertNotIn("fastapi_missing_title_min_length", hidden.output)

            self.assertEqual(clean.exit_code, 0, clean.output)
            self.assertIn("Applied bug seeds: 0 (clean repo)", clean.output)
            clean_schema = (sandbox_root / "bug_test_03/backend/app/schemas/todo.py").read_text(encoding="utf-8")
            self.assertIn("min_length=1", clean_schema)

    @unittest.skipUnless(CliRunner is not None and app is not None, "typer is not installed")
    def test_cli_invalid_bug_request_returns_clear_error(self) -> None:
        assert CliRunner is not None
        assert app is not None
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                app,
                [
                    "init",
                    "bug_test_01",
                    "--sandbox-root",
                    tmp,
                    "--no-setup",
                    "--bug-seed-count",
                    "1",
                    "--bug-category",
                    "does_not_exist",
                ],
            )

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("only 0 are applicable", result.output)


def _init_project(
    sandbox_root: Path,
    *,
    name: str,
    backend_stack: str = "fastapi",
    frontend_stack: str = "react_native",
    bug_seed_count: int = 0,
    bug_seed_random_seed: int | None = None,
    bug_categories: tuple[str, ...] = (),
    bug_hidden: bool = False,
):
    return init_project(
        InitProjectOptions(
            name=name,
            backend_stack=backend_stack,
            frontend_stack=frontend_stack,
            templates_root=TEMPLATES,
            sandbox_root=sandbox_root,
            setup_environment=False,
            bug_seed_count=bug_seed_count,
            bug_seed_random_seed=bug_seed_random_seed,
            bug_categories=bug_categories,
            bug_hidden=bug_hidden,
        )
    )


def _compatible_stacks_for_bug(bug: BugSeed) -> tuple[str, str]:
    backend_matches = [stack for stack in bug.stacks if stack in BACKEND_STACKS]
    if backend_matches:
        return backend_matches[0], "react"
    frontend_matches = [stack for stack in bug.stacks if stack in FRONTEND_STACKS]
    if frontend_matches:
        return "fastapi", frontend_matches[0]
    raise AssertionError(f"Bug seed {bug.id!r} has no supported stack")


def _assert_applied_bug(target: Path, bug: BugSeed) -> None:
    content = (target / bug.relative_path).read_text(encoding="utf-8")
    self = unittest.TestCase()
    self.assertNotIn(bug.old, content)
    self.assertIn(bug.new, content)


def _bug_by_id(bug_id: str) -> BugSeed:
    for bug in BUG_SEEDS:
        if bug.id == bug_id:
            return bug
    raise AssertionError(f"Unknown bug seed id: {bug_id}")


def _bug_project_name(index: int) -> str:
    return f"bug_test_{index:02d}"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
