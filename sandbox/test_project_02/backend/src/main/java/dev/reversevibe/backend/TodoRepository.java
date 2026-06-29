package dev.reversevibe.backend;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

class TodoRepository {
  private final Map<Integer, Todo> todos = new LinkedHashMap<>();
  private int nextId = 1;

  List<Todo> list() { return new ArrayList<>(todos.values()); }

  Todo create(String title) {
    Todo todo = new Todo(nextId, title, false);
    todos.put(nextId, todo);
    nextId += 1;
    return todo;
  }
}
