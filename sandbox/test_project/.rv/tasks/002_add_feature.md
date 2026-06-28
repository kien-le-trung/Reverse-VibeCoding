---
id: "002_add_feature"
title: "Add a successful PATCH todo test"
status: active
goal: "Add test coverage for a successful PATCH /todos/{todo_id} update."
student_actions:
  - "Create or extend backend/tests/test_todos.py."
  - "Use TestClient to create a todo."
  - "Patch that todo's title."
  - "Assert the response status is 200 and the title is updated."
  - "Optionally verify GET /todos returns the updated todo."
evidence_expected:
  - "Passing pytest run for backend/tests/test_todos.py."
  - "New test that proves the successful update path."
mentor_review_focus:
  - "Correct API update behavior."
  - "Test isolation and state management."
  - "Response shape and status code."
files_to_inspect:
  - "backend/app/api/routes/todos.py"
  - "backend/tests/test_todos.py"
files_to_change:
  - "backend/tests/test_todos.py"
completion_check:
  - "Successful PATCH test is committed in backend/tests/test_todos.py."
  - "The relevant pytest command passes."
---

# Task 002: Add a successful PATCH todo test

Goal:
- Add test coverage for a successful `PATCH /todos/{todo_id}` update.

Student actions:
- Create or extend `backend/tests/test_todos.py`.
- Use `TestClient` to create a todo.
- Patch that todo’s title.
- Assert the response status is `200` and the title is updated.
- Optionally verify `GET /todos` returns the updated todo.

Evidence expected:
- Passing pytest run for `backend/tests/test_todos.py`.
- New test that proves the successful update path.

Mentor review focus:
- correct API update behavior
- test isolation and state management
- response shape and status code
