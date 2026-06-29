# Reverse Vibe Coding

Reverse Vibe Coding is a role-reversal workflow for practicing with coding agents.
The AI acts as the operator/reviewer with product intent and review standards; the user implements all code changes.

This repository currently contains the core project-generation frame, reusable starter templates, a Typer CLI, and one generated MVP sandbox project.

## Current Frame

- `src/reverse_vibecoding/`: reusable core package
- `templates/`: starter project templates
- `sandbox/mvp_todo_fullstack/`: generated FastAPI + React Native MVP project
- `generators/`: generation manifests and registry inputs
- `scenarios/`: scenario modifiers
- `rubrics/`: grading and review rubrics
- `prompts/`: operator prompt packs
- `hidden_tests/`: hidden assessment skeletons
- `tests/`: tests for the reusable core

## Development

```bash
python -m pip install -e .
python -m unittest discover -s . -p "test*.py"
```

## CLI

After installing the project in editable mode, generate an MVP project with:

```bash
rev-vib init my_project
```

This composes FastAPI, React Native, SQLite, Todo App, and React Native/FastAPI wiring templates into:

```text
sandbox/my_project/
```

The defaults can be overridden:

```bash
rev-vib init my_project --backend-stack fastapi --frontend-stack react_native --backend-level level_3 --frontend-level level_3
```

During generation, `rev-vib init` prints initialization progress, reads dependency declarations from stack YAML files, writes `requirements.txt`, records frontend dependency metadata, and opens a setup terminal unless `--no-setup` is passed.

Generated projects are clean by default. To create a practice repo with controlled bug seeds, pass a bug count:

```bash
rev-vib init my_project --bug-seed-count 2 --bug-seed-random-seed 123
```

Use `--bug-category validation` to restrict bug selection, `--bug-hidden` to hide bug type and target details from generated metadata, or `--no-bugs` to force a clean repo even when other bug options are present.

The setup terminal runs:

```bash
python -m venv venv
. .\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd mobile
npm install
```

Agent wake-up files are also generated:

```text
.agents/global_prompt.md
sandbox/my_project/.rv/agent_handoff.md
sandbox/my_project/.rv/agent_context.md
sandbox/my_project/.rv/tasks/001_understand_repo.md
sandbox/my_project/.rv/tasks/README.md
sandbox/my_project/.rv/progress/README.md
sandbox/my_project/.rv/file_map.md
sandbox/my_project/.rv/agent_handoff_short.md
sandbox/my_project/AGENTS.md
sandbox/my_project/CLAUDE.md
sandbox/my_project/.github/copilot-instructions.md
sandbox/my_project/.github/instructions/reverse-vibecoding.instructions.md
```

For most IDE agents, paste this line:

```text
Read sandbox/my_project/.rv/agent_handoff.md
```

For short-context or free-tier agents, paste this line:

```text
Read sandbox/my_project/.rv/agent_handoff_short.md
```

Implementation requests are planned in `.rv/tasks/` and completed work summaries are recorded in `.rv/progress/`. The global `.agents/global_guardrails.md` file is automatically referenced by generated handoffs and IDE-native instruction files so the operator is reminded before every response not to implement work directly. Task and progress entries should use the YAML schemas in `.agents/schemas/`. The intended loop is: the operator describes desired behavior, the user inspects and implements, the user reports evidence, the operator reviews, then progress and the next task are recorded.
