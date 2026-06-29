import json

from django.http import JsonResponse
from django.urls import path

_todos: dict[int, dict[str, object]] = {}
_next_id = 1


def health(_request):
    return JsonResponse({"status": "ok"})


def list_or_create_todos(request):
    global _next_id
    if request.method == "GET":
        return JsonResponse(list(_todos.values()), safe=False)
    payload = json.loads(request.body or b"{}")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return JsonResponse({"detail": "Todo title must be 1-120 characters"}, status=400)
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}
    _todos[_next_id] = todo
    _next_id += 1
    return JsonResponse(todo, status=201)


def update_todo(request, todo_id: int):
    if todo_id not in _todos:
        return JsonResponse({"detail": "Todo not found"}, status=404)
    payload = json.loads(request.body or b"{}")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return JsonResponse({"detail": "Todo title must be 1-120 characters"}, status=400)
    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title")}
    return JsonResponse(_todos[todo_id])


urlpatterns = [path("health", health), path("todos", list_or_create_todos), path("todos/<int:todo_id>", update_todo)]
