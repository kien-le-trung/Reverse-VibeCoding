# Project Agent Context

Project: test_project_01
Domain: todo_app
Database: sqlite
Backend: django (level_3)
Frontend: react (level_3)

Generated folders:
- backend/
- mobile/
- .rv/

Applied layers:
- django_base
- level_2
- level_3
- react_base
- level_2
- level_3
- react_django

Suggested checks:
- npm test

Important files:
- .env.example
- .rv/progress/README.md
- .rv/project.json
- .rv/tasks/001_understand_repo.md
- .rv/tasks/README.md
- backend/app/__init__.py
- backend/app/repositories/todo_repository.py
- backend/app/settings.py
- backend/app/urls.py
- backend/manage.py
- backend/pyproject.toml
- backend/README.md
- mobile/index.html
- mobile/package.json
- mobile/README.md
- mobile/src/api/client.ts
- mobile/src/App.tsx
- mobile/src/main.tsx
- README.md
- requirements.txt

Use this file as project context only. Generic operator behavior lives in `.agents/global_prompt.md`, and per-response guardrails live in `.agents/global_guardrails.md`.
