from dataclasses import dataclass
from app.models import Todo

@dataclass(frozen = True)
class TodoItem:
    id: int
    title: str
    completed: bool


class TodoRepository:
    def list(self) -> list[TodoItem]:
        return list(Todo.objects.all().values('id', 'title', 'completed'))

    def create(self, title: str) -> TodoItem:
        object = Todo.objects.create(title=title, completed=False)
        return TodoItem(id=object.id, title=object.title, completed=object.completed)


    def update(self, todo_id: int, title: str, completed: bool) -> TodoItem | None:
        todo = Todo.objects.filter(id=todo_id).first()
        if todo is None:
            return None
        
        if title is not None:
            todo.title = title
        if completed is not None:
            todo.completed = completed
        todo.save()
        return TodoItem(id=todo.id, title=todo.title, completed=todo.completed)