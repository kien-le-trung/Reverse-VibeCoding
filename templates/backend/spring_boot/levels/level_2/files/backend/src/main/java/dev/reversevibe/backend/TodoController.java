package dev.reversevibe.backend;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
class TodoController {
  private final Map<Integer, Todo> todos = new LinkedHashMap<>();
  private int nextId = 1;

  @GetMapping("/todos")
  List<Todo> listTodos() { return new ArrayList<>(todos.values()); }

  @PostMapping("/todos")
  ResponseEntity<Todo> createTodo(@RequestBody TodoRequest request) {
    Todo todo = new Todo(nextId, request.title(), false);
    todos.put(nextId, todo);
    nextId += 1;
    return ResponseEntity.status(HttpStatus.CREATED).body(todo);
  }

  @PatchMapping("/todos/{todoId}")
  ResponseEntity<?> updateTodo(@PathVariable int todoId, @RequestBody TodoRequest request) {
    if (!todos.containsKey(todoId)) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("detail", "Todo not found"));
    Todo updated = new Todo(todoId, request.title(), todos.get(todoId).completed());
    todos.put(todoId, updated);
    return ResponseEntity.ok(updated);
  }
}

record Todo(int id, String title, boolean completed) {}
record TodoRequest(String title) {}
