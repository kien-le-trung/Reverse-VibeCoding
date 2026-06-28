import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.bug_seeds import apply_random_bug_seeds
from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class BugSeedTests(unittest.TestCase):
    def test_apply_random_bug_seed_changes_expected_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            applied = apply_random_bug_seeds(
                target=result.target,
                backend_stack="fastapi",
                frontend_stack="react_native",
                count=1,
                seed=1,
                categories=("validation",),
            )

            schema = (result.target / "backend/app/schemas/todo.py").read_text(encoding="utf-8")

            self.assertEqual(len(applied), 1)
            self.assertEqual(applied[0].id, "fastapi_missing_title_min_length")
            self.assertNotIn("min_length=1", schema)

    def test_init_project_defaults_to_clean_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                )
            )

            schema = (result.target / "backend/app/schemas/todo.py").read_text(encoding="utf-8")
            manifest = (result.target / ".rv/hidden_manifest.json").read_text(encoding="utf-8")

            self.assertEqual(result.bug_seeds, ())
            self.assertIn("min_length=1", schema)
            self.assertIn('"bug_seeds": []', manifest)

    def test_init_project_can_hide_bug_seed_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = init_project(
                InitProjectOptions(
                    name="sample",
                    templates_root=TEMPLATES,
                    sandbox_root=Path(tmp),
                    setup_environment=False,
                    bug_seed_count=1,
                    bug_seed_random_seed=1,
                    bug_categories=("validation",),
                    bug_hidden=True,
                )
            )

            manifest = (result.target / ".rv/hidden_manifest.json").read_text(encoding="utf-8")

            self.assertEqual(len(result.bug_seeds), 1)
            self.assertIn('"bug_hidden": true', manifest)
            self.assertIn('"id": "hidden_bug_1"', manifest)
            self.assertNotIn("fastapi_missing_title_min_length", manifest)


if __name__ == "__main__":
    unittest.main()
