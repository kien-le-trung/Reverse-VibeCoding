type Todo = { id: number; title: string; completed: boolean };
export function TodoList({ todos }: { todos: Todo[] }) {
  return <ul>{todos.map((todo) => <li key={todo.id}>{todo.title} - {todo.completed ? "Done" : "Open"}</li>)}</ul>;
}
