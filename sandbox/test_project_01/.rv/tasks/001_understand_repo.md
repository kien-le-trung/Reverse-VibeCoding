---
id: "001_understand_repo"
title: "Understand the repo"
status: complete
request: "Inspect and summarize the generated todo_app project so the next implementation request is grounded in the repo."
expected_behavior:
  - "The coding agent can identify the backend and frontend responsibilities."
  - "The coding agent can name one missing test, edge case, or design improvement."
implementation_scope:
  - "Inspect files only; do not change product code for this task."
acceptance_criteria:
  - "The coding agent summarizes backend and frontend wiring accurately."
  - "The coding agent identifies one concrete follow-up implementation target."
evidence_required:
  - "Short explanation of backend and mobile responsibilities."
  - "Notes from inspecting the key backend and mobile files."
context:
  - "Confirm the setup terminal completed successfully or run setup manually."
  - "Inspect the backend setup and identify what API tests are missing."
  - "Inspect the API route and repository boundaries."
  - "Inspect how the mobile app calls the backend."
  - "Explain one missing test, edge case, or design improvement."
review_focus:
  - "Repo understanding."
  - "Backend route and repository boundaries."
  - "Missing API test or edge-case identification."
files_to_inspect:
  - "backend/app/main.py"
  - "backend/app/api/routes/todos.py"
  - "backend/app/repositories/todo_repository.py"
  - "mobile/src/api/client.ts"
  - "mobile/src/features/todos/TodoList.tsx"
---

# Task 001: Understand The Repo

Request: Inspect and summarize the generated todo_app project so the next implementation request is grounded in the repo.

Coding agent should:
1. Confirm the setup terminal completed successfully or run setup manually.
2. Inspect the backend setup and identify what API tests are missing.
3. Inspect the API route and repository boundaries.
4. Inspect how the mobile app calls the backend.
5. Explain one missing test, edge case, or design improvement.

Operator instruction:
- Before each response, apply `.agents/global_guardrails.md`.
- Do not edit project files or implement the task directly.
- Ask what the coding agent has run so far.
- Ask the coding agent to explain repo understanding before giving your own interpretation.
- You may explain abstract architecture concepts if that helps clarify the next request.
- Ask for evidence when it helps verify behavior, but keep momentum toward concrete implementation requests.
- When this task is complete, propose the next implementation request and ask the coding agent to add it under `.rv/tasks/`.
- After this task is reviewed, ask the coding agent to add a matching progress entry under `.rv/progress/`.
- Before updating `.rv/tasks/` or `.rv/progress/`, read the matching YAML schema in `.agents/schemas/`.
