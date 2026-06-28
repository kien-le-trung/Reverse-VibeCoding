# Project Agent Context

Project: test_project
Domain: todo_app
Database: sqlite
Backend: fastapi (level_3)
Frontend: react_native (level_3)

Generated folders:
- backend/
- mobile/
- .rv/

Applied layers:
- fastapi_base
- level_2
- level_3
- todo_app
- sqlite
- react_native_base
- level_2
- level_3
- todo_app
- react_native_fastapi

Suggested checks:
- python -m pytest
- npm test

Important files:
- .env.example
- .rv/project.json
- .rv/tasks/001_understand_repo.md
- .rv/tasks/README.md
- backend/app/__init__.py
- backend/app/api/__init__.py
- backend/app/api/routes/__init__.py
- backend/app/api/routes/todos.py
- backend/app/db/__init__.py
- backend/app/db/sqlite.py
- backend/app/main.py
- backend/app/repositories/__init__.py
- backend/app/repositories/todo_repository.py
- backend/app/schemas/__init__.py
- backend/app/schemas/todo.py
- backend/docs/domain.md
- backend/pyproject.toml
- backend/README.md
- backend/tests/test_health.py
- backend/tests/test_todos.py
- mobile/app.json
- mobile/App.tsx
- mobile/package.json
- mobile/README.md

Use this file as project context only. Generic mentor behavior lives in `.agents/prompts/mentor.md`.
