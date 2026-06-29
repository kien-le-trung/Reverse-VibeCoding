import { useEffect, useState, type FormEvent } from "react";

import { getTodos, postTodos, putTodos, type Todo } from "./api/client";

type Screen = "home" | "todos";

export default function App() {
  const [screen, setScreen] = useState<Screen>("todos");
  const [todos, setTodos] = useState<Todo[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (screen !== "todos") {
      return;
    }

    void loadTodos();
  }, [screen]);

  async function loadTodos() {
    setIsLoading(true);
    setError(null);

    try {
      const items = await getTodos();
      setTodos(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load todos");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateTodo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const title = newTitle.trim();
    if (!title) {
      return;
    }

    try {
      const createdTodo = await postTodos(title);
      setTodos((currentTodos) => [createdTodo, ...currentTodos]);
      setNewTitle("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create todo");
    }
  }

  async function handleToggleTodo(todo: Todo) {
    try {
      const updatedTodo = await putTodos(todo.id, todo.title, !todo.completed);
      setTodos((currentTodos) =>
        currentTodos.map((item) => (item.id === todo.id ? updatedTodo : item)),
      );
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update todo");
    }
  }

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem", maxWidth: "40rem", margin: "0 auto", color: "#111827" }}>
      <h1>Reverse Vibe Coding</h1>
      <nav style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <button type="button" onClick={() => setScreen("home")}>Home</button>
        <button type="button" onClick={() => setScreen("todos")}>Todos</button>
      </nav>

      {screen === "home" ? (
        <p>Choose a project screen.</p>
      ) : (
        <section>
          <h2>Todos</h2>
          <form onSubmit={handleCreateTodo} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <input
              value={newTitle}
              onChange={(event) => setNewTitle(event.target.value)}
              placeholder="Add a todo"
              style={{ flex: 1, padding: "0.5rem" }}
            />
            <button type="submit">Add</button>
          </form>

          {error ? <p role="alert">{error}</p> : null}

          {isLoading ? <p>Loading todos...</p> : null}

          {!isLoading && todos.length === 0 ? <p>No todos yet.</p> : null}

          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.5rem" }}>
            {todos.map((todo) => (
              <li key={todo.id} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => void handleToggleTodo(todo)}
                />
                <span style={{ textDecoration: todo.completed ? "line-through" : "none" }}>{todo.title}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
