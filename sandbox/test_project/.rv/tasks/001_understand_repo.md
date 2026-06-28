---
id: "001_understand_repo"
title: "Understand the repo"
status: active
goal: "Understand and verify the generated todo_app project."
student_actions:
  - "Confirm the setup terminal completed successfully or run setup manually."
  - "Inspect the backend setup and identify what API tests are missing."
  - "Inspect the API route and repository boundaries."
  - "Inspect how the mobile app calls the backend."
  - "Explain one missing test, edge case, or design improvement."
evidence_expected:
  - "Short explanation of backend and mobile responsibilities."
  - "Notes from inspecting the key backend and mobile files."
mentor_review_focus:
  - "Repo understanding."
  - "Backend route and repository boundaries."
  - "Missing API test or edge-case identification."
files_to_inspect:
  - "backend/app/main.py"
  - "backend/app/api/routes/todos.py"
  - "backend/app/repositories/todo_repository.py"
  - "mobile/src/api/client.ts"
  - "mobile/src/features/todos/TodoList.tsx"
completion_check:
  - "Student can describe the backend and mobile wiring."
  - "Student can name one missing test, edge case, or design improvement."
---

# Task 001: Understand The Repo

Task: Understand and verify the generated todo_app project.

Student should:
1. Confirm the setup terminal completed successfully or run setup manually.
2. Inspect the backend setup and identify what API tests are missing.
3. Inspect the API route and repository boundaries.
4. Inspect how the mobile app calls the backend.
5. Explain one missing test, edge case, or design improvement.

Mentor instruction:
- Before each response, apply `.agents/mentor_guardrails.md`.
- Do not edit project files or implement the task directly.
- Ask what the student has run so far.
- Ask the student to explain their repo understanding before explaining it yourself.
- Refine the student's explanation from an abstract architecture level.
- Ask for evidence when it helps the student learn, but keep momentum toward reading code and making small changes.
- When this task is complete, propose the next task and ask the student to add it under `.rv/tasks/`.
- After this task is reviewed, ask the student to add a matching progress entry under `.rv/progress/`.
- Before updating `.rv/tasks/` or `.rv/progress/`, read the matching YAML schema in `.agents/schemas/`.
