# Reverse Vibe Coding

Reverse Vibe Coding is an AI-managed software engineering apprenticeship platform.
Students write the software while AI tools act as mentor, reviewer, tech lead, and product manager.

This repository currently contains the core project-generation frame, reusable starter templates, a Typer CLI, and one generated MVP sandbox project.

## Current Frame

- `src/reverse_vibecoding/`: reusable core package
- `templates/`: starter project templates
- `sandbox/mvp_todo_fullstack/`: generated FastAPI + React Native MVP project
- `generators/`: generation manifests and registry inputs
- `scenarios/`: scenario modifiers
- `rubrics/`: grading and review rubrics
- `prompts/`: mentor prompt packs
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
rv init my_project
```

This composes FastAPI, React Native, SQLite, Todo App, and React Native/FastAPI wiring templates into:

```text
sandbox/my_project/
```

The defaults can be overridden:

```bash
rv init my_project --backend-stack fastapi --frontend-stack react_native --backend-level level_3 --frontend-level level_3
```

During generation, `rv init` prints initialization progress, reads dependency declarations from stack YAML files, writes `requirements.txt`, and opens a setup terminal unless `--no-setup` is passed.

The setup terminal runs:

```bash
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Agent wake-up files are also generated:

```text
.agents/prompts/mentor.md
sandbox/my_project/.rv/agent_handoff.md
sandbox/my_project/.rv/agent_context.md
sandbox/my_project/.rv/tasks/001_understand_repo.md
sandbox/my_project/.rv/tasks/README.md
sandbox/my_project/.rv/file_map.md
sandbox/my_project/.rv/agent_handoff_short.md
```

For most IDE agents, paste this line:

```text
Read sandbox/my_project/.rv/agent_handoff.md
```

For short-context or free-tier agents, paste this line:

```text
Read sandbox/my_project/.rv/agent_handoff_short.md
```

Learning work is tracked in `.rv/tasks/`. The intended loop is: explain your repo understanding, refine it with the mentor, implement a focused change, ask for review, then record the next task.

The generated backend has its own checks:

```bash
cd sandbox/mvp_todo_fullstack/backend
python -m pip install -e ".[dev]"
python -m pytest
```
