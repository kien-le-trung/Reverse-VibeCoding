from dataclasses import dataclass

@dataclass(frozen = True)
class TodoItem:
    id: int
    title: str
    completed: bool


class TodoRepository:
    def __init__(self) -> None:
        self._todos: dict[int, TodoItem] = {}
        self._next_id = 1

    def list(self) -> list[TodoItem]:
        return list(self._todos.values())

    def create(self, title: str) -> TodoItem:
        todo = TodoItem(id=self._next_id, title=title, completed=False)
        self._todos[self._next_id] = todo
        self._next_id += 1
        return todo

    def update(self, todo_id: int, title: str, completed: bool) -> TodoItem | None:
        if todo_id in self._todos.keys():
            self._todos[todo_id] = TodoItem(id=todo_id, title=title, completed=completed)
            return self._todos[todo_id]
        return None
