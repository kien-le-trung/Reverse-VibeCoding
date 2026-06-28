"""Core library for Reverse Vibe Coding project generation."""

from reverse_vibecoding.models import (
    CompletenessLevel,
    Database,
    Frontend,
    ProjectSpec,
    Stack,
)
from reverse_vibecoding.template_composer import ComposeResult, TemplateLayer, compose_template_layers
from reverse_vibecoding.template_resolver import ResolvedTemplate, TemplateSelection, resolve_template_layers

__all__ = [
    "CompletenessLevel",
    "ComposeResult",
    "Database",
    "Frontend",
    "ProjectSpec",
    "ResolvedTemplate",
    "Stack",
    "TemplateLayer",
    "TemplateSelection",
    "compose_template_layers",
    "resolve_template_layers",
]
