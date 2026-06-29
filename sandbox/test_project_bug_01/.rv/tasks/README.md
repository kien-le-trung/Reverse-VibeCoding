# Reverse VibeCoding Tasks

This directory tracks implementation requests from the operator to the user.

Task files should be small and concrete. Ask the user to add new files as follow-up work is chosen.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`
- `004_reflect.md`

Each task should include:

- request
- expected behavior
- implementation scope
- acceptance criteria
- evidence required

When creating or updating task files, read `.agents/schemas/task.schema.yaml` and keep the YAML front matter aligned with it.

When a task is complete, ask the user to add or update a matching progress entry under `.rv/progress/`.
