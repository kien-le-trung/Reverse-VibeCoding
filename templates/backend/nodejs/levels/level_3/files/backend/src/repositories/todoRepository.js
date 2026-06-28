class TodoRepository {
  constructor() {
    this.todos = new Map();
    this.nextId = 1;
  }

  list() {
    return Array.from(this.todos.values());
  }

  create(title) {
    const todo = { id: this.nextId, title, completed: false };
    this.todos.set(this.nextId, todo);
    this.nextId += 1;
    return todo;
  }
}

module.exports = { TodoRepository };
