import json

from django.http import JsonResponse
from django.urls import path

from app.repositories.todo_repository import TodoItem, TodoRepository

repository = TodoRepository()


def serialize_todo(todo: TodoItem) -> dict[str, object]:
    return {"id": todo.id, "title": todo.title, "completed": todo.completed}


def health(_request):
    return JsonResponse({"status": "ok"})


def list_or_create_todos(request):
    if request.method == "GET":
        return JsonResponse([serialize_todo(todo) for todo in repository.list()], safe=False)

    payload = json.loads(request.body or b"{}")
    todo = repository.create(title=payload.get("title"))
    return JsonResponse(serialize_todo(todo), status=201)


def update_todo(request, todo_id: int):
    payload = json.loads(request.body or b"{}")
    updated = repository.update(
        todo_id,
        title=payload.get("title"),
        completed=payload.get("completed", False),
    )
    if updated is None:
        return JsonResponse({"detail": "Todo not found"}, status=404)

    return JsonResponse(serialize_todo(updated))


urlpatterns = [path("health", health), path("todos", list_or_create_todos), path("todos/<int:todo_id>", update_todo)]
