# Reverse Vibe Coding

Reverse Vibe Coding is a role-reversal workflow for practicing with coding agents.
The AI acts as the operator/reviewer with product intent and review standards; the user implements all code changes. It is intended to be a lightweight agent-wrapper and a simple project composer intended for learning, developed as a sidequest when I was learning SWE :)

This repository contains the project generator, reusable starter templates, reverse-vibecoding prompts, and tests for the generation system. Developed during time constraints, it is by no means polished, so recommendations are appreciated.

## Repository Layout

- `src/reverse_vibecoding/`: reusable generator package and CLI helpers
- `templates/`: backend, frontend, domain, database, level, bug, and wiring templates
- `.agents/`: global operator prompt, guardrails, schemas, and review rubrics
- `tests/`: tests for template resolution, generation, bug seeding, and CLI helpers
- `sandbox/`: generated practice projects

## Development

Besides the python packages, please ensure you have node.js if you intend to work with React, React Native, Angular; and JDK if you intend to work with Spring Boot.

Install the generator in editable mode:

```bash
python -m pip install -e .
```

Run the test suite:

```bash
python -m unittest discover -s . -p "test*.py"
```

## Quick Start

From the repository root:

```bash
python -m pip install -e .
rev-vib doctor
rev-vib init my_project
```

This creates `sandbox/my_project/`, opens it in a new VS Code window when the `code` CLI is available, and starts dependency installation in the background on Windows. Setup progress is written to:

```text
sandbox/my_project/.rv/setup.log
```

To wake an IDE agent after generation, paste the handoff prompt printed by `rev-vib init`, or run:

```bash
rev-vib open my_project
```

To add the reverse-vibecoding workflow to an existing project:

```bash
rev-vib import C:\absolute\path\to\project
```

## CLI

The package installs one command:

```bash
rev-vib --help
```

Available commands:

```text
init    Generate a new practice project under the sandbox root.
import  Install reverse-vibecoding agent prompts into an existing project
doctor  Check local rev-vib environment readiness.
open    Open a generated or imported project in VS Code.
```

Generate a default sandbox project:

```bash
rev-vib init my_project
```

By default this creates:

```text
sandbox/my_project/
```

The default stack is:

- backend: `fastapi`
- frontend: `react_native`
- database: `sqlite`
- domain: `todo_app`
- backend level: `level_3` (levels explained below)
- frontend level: `level_3` (levels explained below)
- bugs: none

## Init Flags

`rev-vib init` accepts these options:

```text
name                              Project folder name under the sandbox root
--backend-stack TEXT              Backend stack. Default: fastapi
--frontend-stack TEXT             Frontend stack. Default: react_native
--domain TEXT                     Domain overlay. Options: no_domain, todo_app, habit_tracker, expense_tracker. Default: todo_app
--database TEXT                   Backend database overlay. Options: no_database, sqlite, postgresql_local, postgresql_supabase. Default: sqlite
--backend-level TEXT              Backend completeness level. Default: level_3
--frontend-level TEXT             Frontend completeness level. Default: level_3
--templates-root PATH             Template root directory. Default: templates
--sandbox-root PATH               Generated project root directory. Default: sandbox
--force                           Allow overwriting an existing project
--setup / --no-setup              Open project and install dependencies after generation. Default: --setup
--bug-seed-count INTEGER          Number of controlled bug seeds. Default: 0
--bug-seed-random-seed INTEGER    Random seed for reproducible bug selection
--bug-category TEXT               Restrict bug seeds to a category. Can be repeated
--bug-hidden                      Hide selected bug type and target details in metadata
--no-bugs                         Force a clean repo even if bug options are present
```

Supported option values are also printed directly by:

```bash
rev-vib init --help
```

Examples:

```bash
rev-vib init my_project --backend-stack django --frontend-stack react
rev-vib init my_project --backend-stack flask --frontend-stack vue --backend-level level_2
rev-vib init my_project --backend-stack spring_boot --frontend-stack angular --no-setup
rev-vib init level_1_project --backend-level level_1 --frontend-level level_1 --domain no_domain --database no_database
rev-vib init level_2_project --backend-level level_2 --frontend-level level_2 --database no_database
```

Use `--force` only when you intentionally want to replace an existing generated project.

### Init Option Constraints

Some template layers intentionally depend on higher completeness levels:

- Use `--domain no_domain` for level 1 projects.
- Use `--database no_database` for backend levels 1 and 2.
- Domain overlays require both backend and frontend level 2 or higher.
- Database overlays require backend level 3 or higher.

If conflicting flags are passed, `rev-vib init` exits with a message that points out the specific mismatch and suggests the matching `no_domain` or `no_database` option.

## Import Existing Projects

Install the reverse-vibecoding agent workflow into an existing project:

```bash
rev-vib import C:\absolute\path\to\project
```

The import target must be an absolute path to an existing directory. The command copies `.agents/` into the target project, creates `.rv/` task/progress/handoff files, and writes native agent instruction files for Codex, Claude, and Copilot.

Options:

```text
absolute_path_to_project          Absolute path to an existing project directory
--agents-root PATH                Agent support directory to copy. Default: .agents
```

Files written or refreshed:

```text
<project>/.agents/global_prompt.md
<project>/.agents/global_guardrails.md
<project>/.agents/rubrics/engineering_review.md
<project>/.agents/schemas/task.schema.yaml
<project>/.agents/schemas/progress.schema.yaml
<project>/.rv/agent_context.md
<project>/.rv/agent_handoff.md
<project>/.rv/agent_handoff_short.md
<project>/.rv/file_map.md
<project>/.rv/project.json
<project>/.rv/tasks/001_understand_repo.md
<project>/.rv/tasks/README.md
<project>/.rv/progress/README.md
<project>/AGENTS.md
<project>/CLAUDE.md
<project>/.github/copilot-instructions.md
<project>/.github/instructions/reverse-vibecoding.instructions.md
```

After import, start an IDE agent with:

```text
Read <project>/.rv/agent_handoff.md and start the reverse-vibecoding workflow.
```

## Environment Doctor

Check whether the local environment is ready for common `rev-vib` workflows:

```bash
rev-vib doctor
```

`doctor` verifies required project support files such as `.agents/`, `templates/`, and `sandbox/`, checks the Python version, and reports optional tools used by generated projects or editor automation:

```text
code
node
npm
mvn
```

Missing required checks exit with a nonzero status. Missing optional tools are reported as warnings.

Options:

```text
--agents-root PATH                Agent support directory to check. Default: .agents
--templates-root PATH             Template root directory to check. Default: templates
--sandbox-root PATH               Sandbox root directory to check. Default: sandbox
```

## Open Projects

Open a generated or imported project in VS Code and print the handoff prompt:

```bash
rev-vib open my_project
rev-vib open C:\absolute\path\to\project
```

When the argument is a single project name, `rev-vib open` resolves it under `sandbox/`. Use `--sandbox-root` to point at another generated-project root.

Options:

```text
project                           Sandbox project name or path to a generated/imported project
--sandbox-root PATH               Sandbox root used when project is a name. Default: sandbox
```

## Supported Stacks

Backend stacks:

- `fastapi`
- `nodejs`
- `flask`
- `django`
- `spring_boot`

Frontend stacks:

- `react_native`
- `vue`
- `react`
- `angular`

Current domain options:

- `no_domain`
- `todo_app`
- `habit_tracker`
- `expense_tracker`

Use `--domain no_domain` for lower-complexity projects that should not apply a product-domain overlay, including level 1 projects.

Current database options:

- `no_database`
- `sqlite`
- `postgresql_local`
- `postgresql_supabase`

Use `--database no_database` for lower-complexity projects that should not apply a persistence overlay, including level 2 projects.

Completeness levels:

- `level_1`: Minimal starter. Generates the thinnest backend/frontend skeleton for reading, wiring, and first implementation practice. Use `--domain no_domain --database no_database`.
- `level_2`: Basic product shape. Adds more app structure and can use a domain overlay, but should still avoid persistence overlays. Use `--database no_database`.
- `level_3`: Default full practice app. Adds domain behavior, backend persistence, frontend API integration, and enough structure for realistic feature and bug-fix work.
- `level_4`: More complete professional scaffold. Adds the most opinionated structure and setup for advanced practice, larger review surfaces, and stack-specific conventions.

Domain overlays require both backend and frontend level 2 or higher. Database overlays require backend level 3 or higher.

## Setup Behavior

During generation, `rev-vib init`:

1. Resolves backend, frontend, domain, database, level, and wiring templates.
2. Copies template layers into `sandbox/<name>/`.
3. Writes dependency metadata.
4. Writes `requirements.txt` when the backend has Python dependencies.
5. Writes `.rv/frontend_dependencies.json` for frontend dependencies.
6. Applies requested bug seeds.
7. Writes `.rv` project context, tasks, progress folders, and agent handoff files.
8. Writes IDE-native instruction files for Codex, Claude, and Copilot.
9. Opens the generated project in a new VS Code window unless `--no-setup` is passed.
10. Starts dependency installation in the background unless `--no-setup` is passed.

On Windows, the background setup process writes progress to `.rv/setup.log` and runs:

```powershell
python -m venv venv
. .\venv\Scripts\Activate.ps1
if (Test-Path requirements.txt) { python -m pip install -r requirements.txt }
if (Test-Path backend\package.json) { Push-Location backend; npm install; Pop-Location }
if ((Test-Path backend\pom.xml) -and (Get-Command mvn -ErrorAction SilentlyContinue)) { Push-Location backend; mvn dependency:go-offline; Pop-Location }
if (Test-Path mobile\package.json) { Push-Location mobile; npm install; Pop-Location }
```

Each package-manager command runs only when the matching manifest exists. Maven dependency prefetch runs only when `backend/pom.xml` exists and `mvn` is available on `PATH`.

Manual setup:

```powershell
cd sandbox\my_project
python -m venv venv
. .\venv\Scripts\Activate.ps1
if (Test-Path requirements.txt) { python -m pip install -r requirements.txt }
if (Test-Path backend\package.json) { Push-Location backend; npm install; Pop-Location }
if ((Test-Path backend\pom.xml) -and (Get-Command mvn -ErrorAction SilentlyContinue)) { Push-Location backend; mvn dependency:go-offline; Pop-Location }
if (Test-Path mobile\package.json) { Push-Location mobile; npm install; Pop-Location }
```

For non-Python backends, there may be no `requirements.txt`; use the backend README and native package manager for that stack.

## Generated Agent Files

Generated projects include `.rv` workflow files:

```text
sandbox/my_project/.rv/agent_context.md
sandbox/my_project/.rv/agent_handoff.md
sandbox/my_project/.rv/agent_handoff_short.md
sandbox/my_project/.rv/file_map.md
sandbox/my_project/.rv/frontend_dependencies.json
sandbox/my_project/.rv/hidden_manifest.json
sandbox/my_project/.rv/project.json
sandbox/my_project/.rv/tasks/001_understand_repo.md
sandbox/my_project/.rv/tasks/README.md
sandbox/my_project/.rv/progress/README.md
```

Generated projects also include native persistent instruction files:

```text
sandbox/my_project/AGENTS.md
sandbox/my_project/CLAUDE.md
sandbox/my_project/.github/copilot-instructions.md
sandbox/my_project/.github/instructions/reverse-vibecoding.instructions.md
```

These files are generated from `.agents/global_prompt.md` and `.agents/global_guardrails.md`.
They tell IDE agents that the user implements all code changes and the agent acts as operator/reviewer.

To start a session, paste:

```text
Read sandbox/my_project/.rv/agent_handoff.md
```

For short-context agents, paste:

```text
Read sandbox/my_project/.rv/agent_handoff_short.md
```

## Reverse-Vibecoding Workflow

The intended loop is:

1. The operator describes the desired behavior or suspected bug.
2. The user inspects and implements the change.
3. The user reports changed files and evidence.
4. The operator reviews correctness, design, tests, and scope.
5. Task and progress records are updated in `.rv/tasks/` and `.rv/progress/`.

Task files should follow `.agents/schemas/task.schema.yaml`.
Progress files should follow `.agents/schemas/progress.schema.yaml`.
Code review should use `.agents/rubrics/engineering_review.md`.

## Bug Seeding

Generated projects are clean by default. To create a practice repo with controlled bugs:

```bash
rev-vib init bug_project --bug-seed-count 1
```

Use a random seed for reproducibility:

```bash
rev-vib init bug_project --bug-seed-count 2 --bug-seed-random-seed 123
```

Restrict by category:

```bash
rev-vib init bug_project --bug-seed-count 1 --bug-category validation
```

Hide bug details from generated metadata:

```bash
rev-vib init bug_project --bug-seed-count 1 --bug-hidden
```

Force a clean repo even when bug options are present:

```bash
rev-vib init bug_project --bug-seed-count 1 --no-bugs
```

### Bug Categories

Current categories:

- `validation`
- `boundary_status_code`
- `api_integration`
- `http_status`
- `partial_update`
- `response_shape`
- `route_mismatch`
- `environment_config`

### Bug Constraints

Bug seeding follows these rules:

- `--bug-seed-count` must be `0` or greater.
- The requested count cannot exceed applicable bugs for the selected backend/frontend stack.
- A bug applies only when its stack matches either the selected backend or selected frontend.
- The target file must exist.
- The expected clean source snippet must still exist in the file.
- A bug cannot normally be applied twice because the clean snippet is removed after the first application.
- `--bug-category` filters candidates by category and can be passed multiple times.
- `--bug-hidden` hides bug details in `.rv/hidden_manifest.json`, but still applies the bug.
- `--no-bugs` overrides bug options and forces a clean repo.

### Current Max Bugs Per Project

Current registry size: 30 bug seeds.

Maximum applicable bugs per generated project:

- any backend + `react_native`: 8
- any backend + `vue`: 7
- any backend + `react`: 7
- any backend + `angular`: 7

Each backend stack currently has five applicable backend bugs.
React Native currently has three applicable frontend bugs.
Vue, React, and Angular currently have two applicable frontend bugs each.

### Current Bug Seeds

Backend bug seeds:

- `fastapi_missing_title_min_length`
- `nodejs_missing_title_validation`
- `flask_missing_title_validation`
- `django_missing_title_validation`
- `spring_boot_missing_title_validation`
- `fastapi_missing_update_404`
- `nodejs_missing_update_404`
- `flask_missing_update_404`
- `django_missing_update_404`
- `spring_boot_missing_update_404`
- `fastapi_create_returns_200`
- `nodejs_create_returns_200`
- `flask_create_returns_200`
- `django_create_returns_200`
- `spring_boot_create_returns_200`
- `fastapi_update_resets_completed`
- `nodejs_update_resets_completed`
- `flask_update_resets_completed`
- `django_update_resets_completed`
- `spring_boot_update_resets_completed`
- `fastapi_list_response_wrapped`
- `nodejs_list_response_wrapped`
- `flask_list_response_wrapped`
- `django_list_response_wrapped`
- `spring_boot_list_response_wrapped`

Frontend bug seeds:

- `frontend_missing_health_error_check` for React Native
- `frontend_web_missing_health_error_check` for Vue, React, and Angular
- `react_native_wrong_health_endpoint`
- `frontend_web_wrong_health_endpoint` for Vue, React, and Angular
- `react_native_wrong_api_base_url_env`

## Metadata

Generated project metadata lives in:

```text
.rv/project.json
.rv/hidden_manifest.json
.rv/frontend_dependencies.json
```

`.rv/project.json` records selected stacks, levels, dependency metadata, applied layers, bug count, and hidden flag.

`.rv/hidden_manifest.json` records bug seed details unless `--bug-hidden` is used.
When hidden, it records placeholder ids like `hidden_bug_1` and omits the real bug id, file path, category, learning goal, and description.

## Testing The Generator

Run all tests:

```bash
python -m unittest discover -s . -p "test*.py"
```

Focused bug seeding tests:

```bash
python -m unittest tests.test_bug_seeds
```

The bug seeding tests generate temporary sandbox projects with deterministic names like:

```text
bug_test_01
bug_test_02
bug_test_03
```

These are created under temporary directories during tests and are not committed.
