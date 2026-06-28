from app.repositories.todo_repository import TodoRepository


class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    def list_todos(self) -> list[dict[str, object]]:
        return self.repository.list()

    def create_todo(self, title: str) -> dict[str, object]:
        return self.repository.create(title)
