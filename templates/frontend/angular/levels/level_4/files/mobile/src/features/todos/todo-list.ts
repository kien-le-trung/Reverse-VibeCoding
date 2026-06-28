export type Todo = { id: number; title: string; completed: boolean };
export function todoLabel(todo: Todo): string {
  return `${todo.title} - ${todo.completed ? "Done" : "Open"}`;
}
