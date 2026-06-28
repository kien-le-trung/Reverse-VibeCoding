import unittest
from pathlib import Path

from reverse_vibecoding.template_resolver import TemplateSelection, resolve_template_layers


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class TemplateResolverTests(unittest.TestCase):
    def test_fastapi_level_4_expands_through_lower_levels(self) -> None:
        resolved = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="fastapi", level="level_4"),
        )

        self.assertEqual(
            resolved.manifest_ids[:5],
            (
                "fastapi_base",
                "level_1",
                "level_2",
                "level_3",
                "level_4",
            ),
        )
        self.assertEqual(
            tuple(layer.id for layer in resolved.layers),
            (
                "fastapi_base",
                "level_2",
                "level_3",
                "level_4",
            ),
        )

    def test_react_native_level_4_expands_through_lower_levels(self) -> None:
        resolved = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="react_native", level="level_4"),
        )

        self.assertEqual(
            resolved.manifest_ids[:5],
            (
                "react_native_base",
                "level_1",
                "level_2",
                "level_3",
                "level_4",
            ),
        )

    def test_additional_backend_stacks_resolve_through_level_4(self) -> None:
        for stack, base in (
            ("nodejs", "nodejs_base"),
            ("flask", "flask_base"),
            ("django", "django_base"),
            ("spring_boot", "spring_boot_base"),
        ):
            with self.subTest(stack=stack):
                resolved = resolve_template_layers(
                    TEMPLATES,
                    TemplateSelection(stack=stack, level="level_4"),
                )

                self.assertEqual(resolved.manifest_ids[:5], (base, "level_1", "level_2", "level_3", "level_4"))
                self.assertTrue(any(stack in str(layer.source) for layer in resolved.layers))

    def test_additional_frontend_stacks_resolve_through_level_4(self) -> None:
        for stack, base in (
            ("vue", "vue_base"),
            ("react", "react_base"),
            ("angular", "angular_base"),
        ):
            with self.subTest(stack=stack):
                resolved = resolve_template_layers(
                    TEMPLATES,
                    TemplateSelection(stack=stack, level="level_4"),
                )

                self.assertEqual(resolved.manifest_ids[:5], (base, "level_1", "level_2", "level_3", "level_4"))
                self.assertTrue(any(stack in str(layer.source) for layer in resolved.layers))

    def test_database_overlay_checks_minimum_level(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires at least 'level_3'"):
            resolve_template_layers(
                TEMPLATES,
                TemplateSelection(stack="fastapi", level="level_2", databases=("sqlite",)),
            )

    def test_database_overlay_conflicts_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "conflicts"):
            resolve_template_layers(
                TEMPLATES,
                TemplateSelection(
                    stack="fastapi",
                    level="level_3",
                    databases=("sqlite", "postgresql_local"),
                ),
            )

    def test_domain_overlay_resolves_by_stack(self) -> None:
        fastapi = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="fastapi", level="level_2", domains=("todo_app",)),
        )
        react_native = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="react_native", level="level_2", domains=("todo_app",)),
        )

        self.assertTrue(any("fastapi" in str(layer.source) for layer in fastapi.layers))
        self.assertTrue(any("react_native" in str(layer.source) for layer in react_native.layers))

    def test_stack_dependency_declarations_are_resolved(self) -> None:
        fastapi = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="fastapi", level="level_1"),
        )
        react_native = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="react_native", level="level_1"),
        )

        self.assertIn("fastapi>=0.115", fastapi.python_dependencies)
        self.assertIn("expo@^52.0.0", react_native.npm_dependencies)

    def test_new_stack_default_overlays_resolve(self) -> None:
        backend = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="nodejs", level="level_3", domains=("todo_app",), databases=("sqlite",)),
        )
        frontend = resolve_template_layers(
            TEMPLATES,
            TemplateSelection(stack="vue", level="level_3", domains=("todo_app",)),
        )

        self.assertIn("todo_app", backend.manifest_ids)
        self.assertIn("sqlite", backend.manifest_ids)
        self.assertIn("todo_app", frontend.manifest_ids)
        self.assertIn("express@^4.19.2", backend.npm_dependencies)
        self.assertIn("vue@^3.4.0", frontend.npm_dependencies)


if __name__ == "__main__":
    unittest.main()
