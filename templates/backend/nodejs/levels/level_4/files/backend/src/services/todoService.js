class TodoService {
  constructor(repository) {
    this.repository = repository;
  }

  listTodos() {
    return this.repository.list();
  }

  createTodo(title) {
    return this.repository.create(title);
  }
}

module.exports = { TodoService };
