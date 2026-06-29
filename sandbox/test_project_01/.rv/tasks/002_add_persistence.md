---
id: "002_add_persistence"
title: "Add persistent todo storage"
status: active
request: "Replace the in-memory todo storage with persistent backend storage so todos survive reloads and are not lost on server restart."
expected_behavior:
  - "Todos are stored outside process memory so they persist across requests and restarts."
  - "The existing list, create, and update flows continue to work through the backend API."
  - "A focused test or verification demonstrates persistence behavior."
implementation_scope:
  - "Change backend persistence implementation and any directly related tests."
  - "Do not broaden the scope to unrelated frontend work."
acceptance_criteria:
  - "Todo data survives a restart of the backend process."
  - "The repository layer is responsible for persistence rather than module-level state alone."
  - "Relevant backend tests or verification commands pass."
files_to_change:
  - "backend/app/repositories/todo_repository.py"
  - "backend/app/urls.py"
  - "backend/app/tests/test_todo_repository.py"
evidence_required:
  - "Changed file list."
  - "Test or verification output."
  - "Short explanation of how persistence now works."
context:
  - "The current backend uses module-level in-memory storage for todos."
  - "The app is expected to behave like a real todo backend rather than a static in-memory demo."
review_focus:
  - "Persistence correctness."
  - "Clear separation between repository and route handling."
  - "Focused test coverage."
---

Implement persistent todo storage and report back with the evidence.