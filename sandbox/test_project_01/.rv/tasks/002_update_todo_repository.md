---
id: "002_update_todo_repository"
title: "Add update to todo repository"
status: active
request: "Implement repository support for updating existing todos so the backend can persist todo edits consistently."
expected_behavior:
  - "The todo repository exposes an update method for existing todos."
  - "Updating a todo changes the stored title or completion state without breaking list behavior."
  - "The behavior is covered by a focused test or equivalent verification."
implementation_scope:
  - "Change backend repository logic and any directly related tests."
  - "Keep the change scoped to repository support and its immediate integration points."
acceptance_criteria:
  - "A repository update operation succeeds for an existing todo."
  - "A missing todo is handled predictably rather than silently creating invalid state."
  - "Relevant backend tests or verification commands pass."
files_to_change:
  - "backend/app/repositories/todo_repository.py"
  - "backend/tests/test_todo_repository.py"
evidence_required:
  - "Changed file list."
  - "Test or verification output."
  - "Short explanation of how update behavior now works."
context:
  - "The current repository already supports listing and creating todos."
  - "The backend API already exposes update-oriented routes, so the repository layer needs to support that path."
review_focus:
  - "Correct repository semantics."
  - "Predictable handling of missing todos."
  - "Focused test coverage."
---

Implement the repository update path and report back with the relevant evidence.