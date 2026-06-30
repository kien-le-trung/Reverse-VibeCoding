import React, { useState } from "react";

type Screen = "home" | "todos";

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");
  return <main><h1>Reverse Vibe Coding</h1><nav><button onClick={() => setScreen("home")}>Home</button><button onClick={() => setScreen("todos")}>Todos</button></nav>{screen === "home" ? <p>Choose a project screen.</p> : <p>Todo screen placeholder.</p>}</main>;
}
