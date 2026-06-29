const DEFAULT_API_URL = "http://localhost:8000";

export const API_URL = DEFAULT_API_URL;

export interface Todo {
  id: number;
  title: string;
  completed: boolean;
}

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) throw new Error(`Health check failed with ${response.status}`);
  return response.json();
}

export async function getTodos(): Promise<Todo[]> {
  const response = await fetch(`${API_URL}/todos`);
  if (!response.ok) throw new Error(`Failed to fetch todos with ${response.status}`);
  return response.json() as Promise<Todo[]>;
}

export async function postTodos(title: string): Promise<Todo> {
  const response = await fetch(`${API_URL}/todos`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) throw new Error(`Failed to create todo with ${response.status}`);
  return response.json() as Promise<Todo>;
}

export async function putTodos(id: number, title: string, completed: boolean): Promise<Todo> {
  const response = await fetch(`${API_URL}/todos/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title, completed }),
  });
  if (!response.ok) throw new Error(`Failed to update todo with ${response.status}`);
  return response.json() as Promise<Todo>;
}