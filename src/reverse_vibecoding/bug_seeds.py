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
  const updated = { ...todos.get(todoId), title: req.body.title };''',
        new="  const updated = { ...todos.get(todoId), title: req.body.title };",
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
    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());''',
        new="    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());",
        learning_goal="Controllers should return intentional client errors for missing resources.",
        description="PATCH /todos/{todoId} no longer handles missing todos explicitly.",
    ),
    BugSeed(
        id="frontend_missing_health_error_check",
        category="api_integration",
        stacks=("react_native", "vue", "react", "angular"),
        relative_path="mobile/src/api/client.ts",
        old='''  if (!response.ok) {
    throw new Error(`Health check failed with ${response.status}`);
  }
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
    if count > len(candidates):
        raise ValueError(f"Requested {count} bug seeds, but only {len(candidates)} are applicable")

    rng = random.Random(seed)
    selected = rng.sample(candidates, count)
    return tuple(_apply_bug_seed(target, bug) for bug in selected)


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
