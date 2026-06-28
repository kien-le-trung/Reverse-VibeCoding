from fastapi import FastAPI

from app.api.routes.todos import router as todos_router

app = FastAPI(title="Reverse Vibe Coding Backend")
app.include_router(todos_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
