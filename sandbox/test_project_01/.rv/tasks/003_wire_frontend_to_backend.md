---
id: "003_wire_frontend_to_backend"
title: "Wire frontend to backend"
status: active
request: "Connect the React frontend to the Django backend so todo operations use the real API instead of local-only behavior."
expected_behavior:
  - "The frontend calls the backend API for listing, creating, and updating todos."
  - "The UI reflects backend responses and handles basic error states."
  - "The integration is covered by a focused verification step."
implementation_scope:
  - "Change frontend API integration and any directly related UI logic."
  - "Keep the change scoped to wiring the existing frontend to the backend."
acceptance_criteria:
  - "Todo list data is fetched from the backend."
  - "Creating and updating todos reaches the backend API."
  - "Relevant frontend verification or test output is provided."
files_to_change:
  - "mobile/src/api/client.ts"
  - "mobile/src/App.tsx"
  - "mobile/src/features/todos/TodoList.tsx"
evidence_required:
  - "Changed file list."
  - "Verification output from the relevant frontend check."
  - "Short explanation of how the frontend now talks to the backend."
context:
  - "The backend now exposes todo CRUD-style behavior through its routes and repository."
  - "The frontend currently has a basic React app and API client scaffolding."
review_focus:
  - "Correct API integration."
  - "Error handling and state updates."
  - "Scope control and maintainability."
---

Implement the frontend-to-backend wiring and report back with the relevant evidence.