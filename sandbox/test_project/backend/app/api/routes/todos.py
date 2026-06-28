from fastapi import APIRouter, HTTPException, status

from app.schemas.todo import TodoCreate, TodoRead

router = APIRouter(prefix="/todos", tags=["todos"])

_todos: dict[int, TodoRead] = {}
_next_id = 1


@router.get("", response_model=list[TodoRead])
def list_todos() -> list[TodoRead]:
    return list(_todos.values())


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate) -> TodoRead:
    global _next_id
    todo = TodoRead(id=_next_id, title=payload.title, completed=False)
    _todos[todo.id] = todo
    _next_id += 1
    return todo


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, payload: TodoCreate) -> TodoRead:
    if todo_id not in _todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    existing = _todos[todo_id]
    updated = existing.model_copy(update={"title": payload.title})
    _todos[todo_id] = updated
    return updated

