from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import TodoRead


class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    def list_todos(self) -> list[TodoRead]:
        return self.repository.list()

    def create_todo(self, title: str) -> TodoRead:
        return self.repository.create(title=title)

