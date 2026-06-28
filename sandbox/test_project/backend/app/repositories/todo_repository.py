from app.schemas.todo import TodoRead


class TodoRepository:
    """Persistence boundary for todo data.

    The starter implementation remains in memory. Database overlays replace or extend this class.
    """

    def __init__(self) -> None:
        self._todos: dict[int, TodoRead] = {}
        self._next_id = 1

    def list(self) -> list[TodoRead]:
        return list(self._todos.values())

    def create(self, title: str) -> TodoRead:
        todo = TodoRead(id=self._next_id, title=title, completed=False)
        self._todos[todo.id] = todo
        self._next_id += 1
        return todo

