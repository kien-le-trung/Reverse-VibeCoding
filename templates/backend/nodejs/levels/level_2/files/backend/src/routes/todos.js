const { Router } = require("express");

const router = Router();
const todos = new Map();
let nextId = 1;

router.get("/todos", (_req, res) => res.json(Array.from(todos.values())));

router.post("/todos", (req, res) => {
  const todo = { id: nextId, title: req.body.title, completed: false };
  todos.set(nextId, todo);
  nextId += 1;
  res.status(201).json(todo);
});

router.patch("/todos/:todoId", (req, res) => {
  const todoId = Number(req.params.todoId);
  if (!todos.has(todoId)) {
    res.status(404).json({ detail: "Todo not found" });
    return;
  }
  const updated = { ...todos.get(todoId), title: req.body.title };
  todos.set(todoId, updated);
  res.json(updated);
});

module.exports = router;
