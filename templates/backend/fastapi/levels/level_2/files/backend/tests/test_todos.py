from fastapi.testclient import TestClient

from app.main import app


def test_create_and_list_todos() -> None:
    client = TestClient(app)

    created = client.post("/todos", json={"title": "Write a failing test"})

    assert created.status_code == 201
    assert created.json()["title"] == "Write a failing test"

    listed = client.get("/todos")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
