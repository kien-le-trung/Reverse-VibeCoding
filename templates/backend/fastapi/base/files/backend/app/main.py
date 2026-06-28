from fastapi import FastAPI

app = FastAPI(title="Reverse Vibe Coding Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

