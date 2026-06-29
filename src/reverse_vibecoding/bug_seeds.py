"""Controlled stochastic bug seeding for generated projects."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BugSeed:
    id: str
    category: str
    stacks: tuple[str, ...]
    relative_path: str
    old: str
    new: str
    learning_goal: str
    description: str


@dataclass(frozen=True)
class AppliedBugSeed:
    id: str
    category: str
    relative_path: str
    learning_goal: str
    description: str


BUG_SEEDS: tuple[BugSeed, ...] = (
    BugSeed(
        id="fastapi_missing_title_min_length",
        category="validation",
        stacks=("fastapi",),
        relative_path="backend/app/schemas/todo.py",
        old="title: str = Field(min_length=1, max_length=120)",
        new="title: str = Field(max_length=120)",
        learning_goal="Input validation belongs at the API boundary.",
        description="Todo title no longer rejects empty strings.",
    ),
    BugSeed(
        id="nodejs_missing_title_validation",
        category="validation",
        stacks=("nodejs",),
        relative_path="backend/src/routes/todos.js",
        old='''router.post("/todos", (req, res) => {
  if (typeof req.body.title !== "string" || req.body.title.trim() === "" || req.body.title.length > 120) {
    res.status(400).json({ detail: "Todo title must be 1-120 characters" });
    return;
  }
  const todo = { id: nextId, title: req.body.title, completed: false };''',
        new='''router.post("/todos", (req, res) => {
  const todo = { id: nextId, title: req.body.title, completed: false };''',
        learning_goal="Input validation belongs at the API boundary.",
        description="Todo title no longer rejects empty or oversized strings.",
    ),
    BugSeed(
        id="flask_missing_title_validation",
        category="validation",
        stacks=("flask",),
        relative_path="backend/app/main.py",
        old='''    payload = request.get_json() or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return jsonify({"detail": "Todo title must be 1-120 characters"}), 400
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}''',
        new='''    payload = request.get_json() or {}
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}''',
        learning_goal="Input validation belongs at the API boundary.",
        description="Todo title no longer rejects empty or oversized strings.",
    ),
    BugSeed(
        id="django_missing_title_validation",
        category="validation",
        stacks=("django",),
        relative_path="backend/app/urls.py",
        old='''    payload = json.loads(request.body or b"{}")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return JsonResponse({"detail": "Todo title must be 1-120 characters"}, status=400)
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}''',
        new='''    payload = json.loads(request.body or b"{}")
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}''',
        learning_goal="Input validation belongs at the API boundary.",
        description="Todo title no longer rejects empty or oversized strings.",
    ),
    BugSeed(
        id="spring_boot_missing_title_validation",
        category="validation",
        stacks=("spring_boot",),
        relative_path="backend/src/main/java/dev/reversevibe/backend/TodoController.java",
        old='''  ResponseEntity<?> createTodo(@RequestBody TodoRequest request) {
    if (request.title() == null || request.title().trim().isEmpty() || request.title().length() > 120) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("detail", "Todo title must be 1-120 characters"));
    }
    Todo todo = new Todo(nextId, request.title(), false);''',
        new='''  ResponseEntity<?> createTodo(@RequestBody TodoRequest request) {
    Todo todo = new Todo(nextId, request.title(), false);''',
        learning_goal="Input validation belongs at the API boundary.",
        description="Todo title no longer rejects empty or oversized strings.",
    ),
    BugSeed(
        id="fastapi_missing_update_404",
        category="boundary_status_code",
        stacks=("fastapi",),
        relative_path="backend/app/api/routes/todos.py",
        old='''    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    existing = _todos[todo_id]''',
        new="    existing = _todos[todo_id]",
        learning_goal="Missing resources should return deliberate 404 responses, not accidental server errors.",
        description="PATCH /todos/{todo_id} no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="nodejs_missing_update_404",
        category="boundary_status_code",
        stacks=("nodejs",),
        relative_path="backend/src/routes/todos.js",
        old='''  if (!todos.has(todoId)) {
    res.status(404).json({ detail: "Todo not found" });
    return;
  }
  if (typeof req.body.title !== "string" || req.body.title.trim() === "" || req.body.title.length > 120) {
    res.status(400).json({ detail: "Todo title must be 1-120 characters" });
    return;
  }
  const updated = { ...todos.get(todoId), title: req.body.title };''',
        new='''  if (typeof req.body.title !== "string" || req.body.title.trim() === "" || req.body.title.length > 120) {
    res.status(400).json({ detail: "Todo title must be 1-120 characters" });
    return;
  }
  const updated = { ...todos.get(todoId), title: req.body.title };''',
        learning_goal="Route handlers should make missing-resource behavior explicit.",
        description="PATCH /todos/:todoId no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="flask_missing_update_404",
        category="boundary_status_code",
        stacks=("flask",),
        relative_path="backend/app/main.py",
        old='''    if todo_id not in _todos:
        return jsonify({"detail": "Todo not found"}), 404
    payload = request.get_json() or {}''',
        new="    payload = request.get_json() or {}",
        learning_goal="Route handlers should return intentional client errors for missing resources.",
        description="PATCH /todos/<todo_id> no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="django_missing_update_404",
        category="boundary_status_code",
        stacks=("django",),
        relative_path="backend/app/urls.py",
        old='''    if todo_id not in _todos:
        return JsonResponse({"detail": "Todo not found"}, status=404)
    payload = json.loads(request.body or b"{}")''',
        new='    payload = json.loads(request.body or b"{}")',
        learning_goal="Views should return intentional client errors for missing resources.",
        description="PATCH-like todo update no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="spring_boot_missing_update_404",
        category="boundary_status_code",
        stacks=("spring_boot",),
        relative_path="backend/src/main/java/dev/reversevibe/backend/TodoController.java",
        old='''    if (!todos.containsKey(todoId)) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("detail", "Todo not found"));
    if (request.title() == null || request.title().trim().isEmpty() || request.title().length() > 120) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("detail", "Todo title must be 1-120 characters"));
    }
    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());''',
        new='''    if (request.title() == null || request.title().trim().isEmpty() || request.title().length() > 120) {
      return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("detail", "Todo title must be 1-120 characters"));
    }
    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());''',
        learning_goal="Controllers should return intentional client errors for missing resources.",
        description="PATCH /todos/{todoId} no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="fastapi_create_returns_200",
        category="http_status",
        stacks=("fastapi",),
        relative_path="backend/app/api/routes/todos.py",
        old="@router.post(\"\", response_model=TodoRead, status_code=status.HTTP_201_CREATED)",
        new="@router.post(\"\", response_model=TodoRead)",
        learning_goal="Successful creates should use intentional HTTP status codes.",
        description="POST /todos returns 200 instead of 201 Created.",
    ),
    BugSeed(
        id="nodejs_create_returns_200",
        category="http_status",
        stacks=("nodejs",),
        relative_path="backend/src/routes/todos.js",
        old="  res.status(201).json(todo);",
        new="  res.json(todo);",
        learning_goal="Successful creates should use intentional HTTP status codes.",
        description="POST /todos returns 200 instead of 201 Created.",
    ),
    BugSeed(
        id="flask_create_returns_200",
        category="http_status",
        stacks=("flask",),
        relative_path="backend/app/main.py",
        old="    return jsonify(todo), 201",
        new="    return jsonify(todo)",
        learning_goal="Successful creates should use intentional HTTP status codes.",
        description="POST /todos returns 200 instead of 201 Created.",
    ),
    BugSeed(
        id="django_create_returns_200",
        category="http_status",
        stacks=("django",),
        relative_path="backend/app/urls.py",
        old="    return JsonResponse(todo, status=201)",
        new="    return JsonResponse(todo)",
        learning_goal="Successful creates should use intentional HTTP status codes.",
        description="POST /todos returns 200 instead of 201 Created.",
    ),
    BugSeed(
        id="spring_boot_create_returns_200",
        category="http_status",
        stacks=("spring_boot",),
        relative_path="backend/src/main/java/dev/reversevibe/backend/TodoController.java",
        old="    return ResponseEntity.status(HttpStatus.CREATED).body(todo);",
        new="    return ResponseEntity.ok(todo);",
        learning_goal="Successful creates should use intentional HTTP status codes.",
        description="POST /todos returns 200 instead of 201 Created.",
    ),
    BugSeed(
        id="fastapi_update_resets_completed",
        category="partial_update",
        stacks=("fastapi",),
        relative_path="backend/app/api/routes/todos.py",
        old='    updated = existing.model_copy(update={"title": payload.title})',
        new='    updated = existing.model_copy(update={"title": payload.title, "completed": False})',
        learning_goal="Partial updates should preserve fields that were not requested.",
        description="PATCH /todos/{todo_id} resets completed to false while updating title.",
    ),
    BugSeed(
        id="nodejs_update_resets_completed",
        category="partial_update",
        stacks=("nodejs",),
        relative_path="backend/src/routes/todos.js",
        old="  const updated = { ...todos.get(todoId), title: req.body.title };",
        new="  const updated = { ...todos.get(todoId), title: req.body.title, completed: false };",
        learning_goal="Partial updates should preserve fields that were not requested.",
        description="PATCH /todos/:todoId resets completed to false while updating title.",
    ),
    BugSeed(
        id="flask_update_resets_completed",
        category="partial_update",
        stacks=("flask",),
        relative_path="backend/app/main.py",
        old='    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title")}',
        new='    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title"), "completed": False}',
        learning_goal="Partial updates should preserve fields that were not requested.",
        description="PATCH /todos/<todo_id> resets completed to false while updating title.",
    ),
    BugSeed(
        id="django_update_resets_completed",
        category="partial_update",
        stacks=("django",),
        relative_path="backend/app/urls.py",
        old='    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title")}',
        new='    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title"), "completed": False}',
        learning_goal="Partial updates should preserve fields that were not requested.",
        description="PATCH-like todo update resets completed to false while updating title.",
    ),
    BugSeed(
        id="spring_boot_update_resets_completed",
        category="partial_update",
        stacks=("spring_boot",),
        relative_path="backend/src/main/java/dev/reversevibe/backend/TodoController.java",
        old="    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());",
        new="    Todo updated = new Todo(todoId, request.title(), false);",
        learning_goal="Partial updates should preserve fields that were not requested.",
        description="PATCH /todos/{todoId} resets completed to false while updating title.",
    ),
    BugSeed(
        id="fastapi_list_response_wrapped",
        category="response_shape",
        stacks=("fastapi",),
        relative_path="backend/app/api/routes/todos.py",
        old='''@router.get("", response_model=list[TodoRead])
def list_todos() -> list[TodoRead]:
    return list(_todos.values())''',
        new='''@router.get("")
def list_todos() -> dict[str, list[TodoRead]]:
    return {"todos": list(_todos.values())}''',
        learning_goal="Backend responses should match the API contract expected by clients.",
        description="GET /todos returns an object wrapper instead of the todo array.",
    ),
    BugSeed(
        id="nodejs_list_response_wrapped",
        category="response_shape",
        stacks=("nodejs",),
        relative_path="backend/src/routes/todos.js",
        old='router.get("/todos", (_req, res) => res.json(Array.from(todos.values())));',
        new='router.get("/todos", (_req, res) => res.json({ todos: Array.from(todos.values()) }));',
        learning_goal="Backend responses should match the API contract expected by clients.",
        description="GET /todos returns an object wrapper instead of the todo array.",
    ),
    BugSeed(
        id="flask_list_response_wrapped",
        category="response_shape",
        stacks=("flask",),
        relative_path="backend/app/main.py",
        old="    return jsonify(list(_todos.values()))",
        new='    return jsonify({"todos": list(_todos.values())})',
        learning_goal="Backend responses should match the API contract expected by clients.",
        description="GET /todos returns an object wrapper instead of the todo array.",
    ),
    BugSeed(
        id="django_list_response_wrapped",
        category="response_shape",
        stacks=("django",),
        relative_path="backend/app/urls.py",
        old="        return JsonResponse(list(_todos.values()), safe=False)",
        new='        return JsonResponse({"todos": list(_todos.values())})',
        learning_goal="Backend responses should match the API contract expected by clients.",
        description="GET /todos returns an object wrapper instead of the todo array.",
    ),
    BugSeed(
        id="spring_boot_list_response_wrapped",
        category="response_shape",
        stacks=("spring_boot",),
        relative_path="backend/src/main/java/dev/reversevibe/backend/TodoController.java",
        old='''  @GetMapping("/todos")
  List<Todo> listTodos() { return new ArrayList<>(todos.values()); }''',
        new='''  @GetMapping("/todos")
  Map<String, List<Todo>> listTodos() { return Map.of("todos", new ArrayList<>(todos.values())); }''',
        learning_goal="Backend responses should match the API contract expected by clients.",
        description="GET /todos returns an object wrapper instead of the todo array.",
    ),
    BugSeed(
        id="react_native_wrong_health_endpoint",
        category="route_mismatch",
        stacks=("react_native",),
        relative_path="mobile/src/api/client.ts",
        old='  const response = await fetch(`${API_URL}/health`);',
        new='  const response = await fetch(`${API_URL}/api/health`);',
        learning_goal="Frontend clients and backend routes must agree on endpoint paths.",
        description="The frontend health client calls /api/health while the backend exposes /health.",
    ),
    BugSeed(
        id="frontend_web_wrong_health_endpoint",
        category="route_mismatch",
        stacks=("vue", "react", "angular"),
        relative_path="mobile/src/api/client.ts",
        old='  const response = await fetch(`${API_URL}/health`);',
        new='  const response = await fetch(`${API_URL}/api/health`);',
        learning_goal="Frontend clients and backend routes must agree on endpoint paths.",
        description="The frontend health client calls /api/health while the backend exposes /health.",
    ),
    BugSeed(
        id="react_native_wrong_api_base_url_env",
        category="environment_config",
        stacks=("react_native",),
        relative_path="mobile/src/api/client.ts",
        old="export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? DEFAULT_API_URL;",
        new="export const API_URL = process.env.API_URL ?? DEFAULT_API_URL;",
        learning_goal="Frontend frameworks have specific environment variable conventions.",
        description="React Native reads API_URL instead of EXPO_PUBLIC_API_URL.",
    ),
    BugSeed(
        id="frontend_missing_health_error_check",
        category="api_integration",
        stacks=("react_native",),
        relative_path="mobile/src/api/client.ts",
        old='''  if (!response.ok) {
    throw new Error(`Health check failed with ${response.status}`);
  }
  return response.json();''',
        new="  return response.json();",
        learning_goal="Frontend API clients should handle non-2xx responses deliberately.",
        description="The health API client no longer checks response.ok before parsing JSON.",
    ),
    BugSeed(
        id="frontend_web_missing_health_error_check",
        category="api_integration",
        stacks=("vue", "react", "angular"),
        relative_path="mobile/src/api/client.ts",
        old='''  if (!response.ok) throw new Error(`Health check failed with ${response.status}`);
  return response.json();''',
        new="  return response.json();",
        learning_goal="Frontend API clients should handle non-2xx responses deliberately.",
        description="The health API client no longer checks response.ok before parsing JSON.",
    ),
)


def apply_random_bug_seeds(
    *,
    target: Path,
    backend_stack: str,
    frontend_stack: str,
    count: int,
    seed: int | None = None,
    categories: tuple[str, ...] = (),
) -> tuple[AppliedBugSeed, ...]:
    if count < 0:
        raise ValueError("bug_seed_count must be non-negative")
    if count == 0:
        return ()

    category_set = set(categories)
    candidates = [
        bug
        for bug in BUG_SEEDS
        if _is_applicable(bug, target, backend_stack, frontend_stack)
        and (not category_set or bug.category in category_set)
    ]

    rng = random.Random(seed)
    rng.shuffle(candidates)
    applied: list[AppliedBugSeed] = []
    for bug in candidates:
        if len(applied) == count:
            break
        if _is_applicable(bug, target, backend_stack, frontend_stack):
            applied.append(_apply_bug_seed(target, bug))

    if len(applied) < count:
        raise ValueError(f"Requested {count} bug seeds, but only {len(applied)} are applicable")
    return tuple(applied)


def _is_applicable(bug: BugSeed, target: Path, backend_stack: str, frontend_stack: str) -> bool:
    if backend_stack not in bug.stacks and frontend_stack not in bug.stacks:
        return False
    path = target / bug.relative_path
    return path.exists() and bug.old in path.read_text(encoding="utf-8")


def _apply_bug_seed(target: Path, bug: BugSeed) -> AppliedBugSeed:
    path = target / bug.relative_path
    content = path.read_text(encoding="utf-8")
    if bug.old not in content:
        raise ValueError(f"Bug seed {bug.id!r} target text not found in {bug.relative_path}")
    path.write_text(content.replace(bug.old, bug.new, 1), encoding="utf-8")
    return AppliedBugSeed(
        id=bug.id,
        category=bug.category,
        relative_path=bug.relative_path,
        learning_goal=bug.learning_goal,
        description=bug.description,
    )
