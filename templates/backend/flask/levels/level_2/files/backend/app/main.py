from flask import Flask, jsonify, request

app = Flask(__name__)
_todos: dict[int, dict[str, object]] = {}
_next_id = 1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/todos")
def list_todos():
    return jsonify(list(_todos.values()))


@app.post("/todos")
def create_todo():
    global _next_id
    payload = request.get_json() or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return jsonify({"detail": "Todo title must be 1-120 characters"}), 400
    todo = {"id": _next_id, "title": payload.get("title"), "completed": False}
    _todos[_next_id] = todo
    _next_id += 1
    return jsonify(todo), 201


@app.patch("/todos/<int:todo_id>")
def update_todo(todo_id: int):
    if todo_id not in _todos:
        return jsonify({"detail": "Todo not found"}), 404
    payload = request.get_json() or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        return jsonify({"detail": "Todo title must be 1-120 characters"}), 400
    _todos[todo_id] = {**_todos[todo_id], "title": payload.get("title")}
    return jsonify(_todos[todo_id])
