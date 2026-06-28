from fastapi.testclient import TestClient

from app.main import app


def test_create_and_list_todos() -> None:
    client = TestClient(app)

    created = client.post("/todos", json={"title": "Write an API test"})

    assert created.status_code == 201
    assert created.json()["title"] == "Write an API test"
    assert created.json()["completed"] is False

    listed = client.get("/todos")

    assert listed.status_code == 200
    assert any(todo["title"] == "Write an API test" for todo in listed.json())


def test_update_missing_todo_returns_404() -> None:
    client = TestClient(app)

    response = client.patch("/todos/999", json={"title": "Missing todo"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}
