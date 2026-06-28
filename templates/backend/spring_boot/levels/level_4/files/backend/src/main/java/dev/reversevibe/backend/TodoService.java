package dev.reversevibe.backend;

import java.util.List;

class TodoService {
  private final TodoRepository repository;

  TodoService(TodoRepository repository) { this.repository = repository; }
  List<Todo> listTodos() { return repository.list(); }
  Todo createTodo(String title) { return repository.create(title); }
}
