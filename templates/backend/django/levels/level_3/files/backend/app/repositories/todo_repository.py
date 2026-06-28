class TodoRepository:
    def __init__(self) -> None:
        self._todos: dict[int, dict[str, object]] = {}
        self._next_id = 1

    def list(self) -> list[dict[str, object]]:
        return list(self._todos.values())

    def create(self, title: str) -> dict[str, object]:
        todo = {"id": self._next_id, "title": title, "completed": False}
        self._todos[self._next_id] = todo
        self._next_id += 1
        return todo
