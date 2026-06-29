import json
import unittest
from pathlib import Path

from reverse_vibecoding.template_resolver import _parse_simple_yaml
from reverse_vibecoding.template_resolver import TemplateSelection, resolve_template_layers


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def _package_dependencies(dependencies: dict[str, str]) -> set[str]:
    return {f"{name}@{version}" for name, version in dependencies.items()}


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
        expectations = {
            "fastapi": ("python_dependencies", "fastapi>=0.115"),
            "flask": ("python_dependencies", "flask>=3.0"),
            "django": ("python_dependencies", "django>=5.0"),
            "nodejs": ("npm_dependencies", "express@^4.19.2"),
            "spring_boot": ("maven_dependencies", "org.springframework.boot:spring-boot-starter-web:3.3.0"),
            "react_native": ("npm_dependencies", "expo@^52.0.0"),
            "vue": ("npm_dependencies", "vue@^3.4.0"),
            "react": ("npm_dependencies", "react@^18.3.1"),
            "angular": ("npm_dependencies", "@angular/core@^18.0.0"),
        }

        for stack, (field_name, expected_dependency) in expectations.items():
            with self.subTest(stack=stack):
                resolved = resolve_template_layers(
                    TEMPLATES,
                    TemplateSelection(stack=stack, level="level_1"),
                )

                self.assertIn(expected_dependency, getattr(resolved, field_name))

    def test_frontend_dev_dependency_declarations_are_resolved(self) -> None:
        expectations = {
            "react_native": "@types/react@~18.3.12",
            "vue": "typescript@^5.6.3",
            "react": "@types/react@^18.3.0",
            "angular": "@angular/cli@^18.0.0",
        }

        for stack, expected_dependency in expectations.items():
            with self.subTest(stack=stack):
                resolved = resolve_template_layers(
                    TEMPLATES,
                    TemplateSelection(stack=stack, level="level_1"),
                )

                self.assertIn(expected_dependency, resolved.npm_dev_dependencies)

    def test_frontend_base_package_json_matches_overlay_dependencies(self) -> None:
        for package_path in sorted(TEMPLATES.glob("frontend/*/base/files/mobile/package.json")):
            stack = package_path.parts[-5]
            overlay_path = TEMPLATES / "frontend" / stack / "base" / "overlay.yaml"
            package_json = json.loads(package_path.read_text(encoding="utf-8"))
            overlay = _parse_simple_yaml(overlay_path.read_text(encoding="utf-8"))

            package_dependencies = _package_dependencies(package_json.get("dependencies", {}))
            package_dev_dependencies = _package_dependencies(package_json.get("devDependencies", {}))

            self.assertEqual(
                package_dependencies,
                set(overlay.get("npm_dependencies", [])),
                f"{stack} npm_dependencies drift from package.json",
            )
            self.assertEqual(
                package_dev_dependencies,
                set(overlay.get("npm_dev_dependencies", [])),
                f"{stack} npm_dev_dependencies drift from package.json",
            )

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
