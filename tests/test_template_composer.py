import tempfile
import unittest
from pathlib import Path

from reverse_vibecoding.template_composer import TemplateLayer, compose_template_layers


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class TemplateComposerTests(unittest.TestCase):
    def test_fastapi_level_overwrites_base_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = compose_template_layers(
                [
                    TemplateLayer("fastapi_base", TEMPLATES / "backend/fastapi/base/files"),
                    TemplateLayer("level_2", TEMPLATES / "backend/fastapi/levels/level_2/files"),
                ],
                target,
            )

            main = (target / "backend/app/main.py").read_text(encoding="utf-8")

            self.assertEqual(result.applied_layers, ("fastapi_base", "level_2"))
            self.assertIn("include_router(todos_router)", main)
            self.assertTrue((target / "backend/tests/test_health.py").exists())
            self.assertTrue((target / "backend/tests/test_todos.py").exists())

    def test_react_native_level_overwrites_base_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            compose_template_layers(
                [
                    TemplateLayer("react_native_base", TEMPLATES / "frontend/react_native/base/files"),
                    TemplateLayer(
                        "level_2",
                        TEMPLATES / "frontend/react_native/levels/level_2/files",
                    ),
                    TemplateLayer(
                        "level_3",
                        TEMPLATES / "frontend/react_native/levels/level_3/files",
                    ),
                ],
                target,
            )

            app = (target / "mobile/App.tsx").read_text(encoding="utf-8")

            self.assertIn('type Screen = "home" | "todos"', app)
            self.assertTrue((target / "mobile/src/api/client.ts").exists())
            self.assertTrue((target / "mobile/src/env.d.ts").exists())

    def test_missing_layer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                compose_template_layers(
                    [TemplateLayer("missing", TEMPLATES / "missing/files")],
                    Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
