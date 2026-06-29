import pytest

from app.repositories.todo_repository import TodoItem, TodoRepository

pytestmark = pytest.mark.django_db

def test_update_existing_todo_changes_stored_fields() -> None:
    repository = TodoRepository()
    todo = repository.create("Draft title")

    updated = repository.update(todo.id, title="Final title", completed=True)

    assert updated is not None
    assert updated.id == todo.id
    assert updated.title == "Final title"
    assert updated.completed is True


def test_update_existing_todo_is_reflected_in_list() -> None:
    repository = TodoRepository()
    todo = repository.create("Draft title")

    repository.update(todo.id, title="Final title", completed=True)

    assert repository.list() == [
        TodoItem(id=todo.id, title="Final title", completed=True)
    ]


def test_update_missing_todo_returns_none() -> None:
    repository = TodoRepository()

    updated = repository.update(999, title="Missing", completed=True)

    assert updated is None
    assert repository.list() == []
