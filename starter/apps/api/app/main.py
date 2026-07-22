from fastapi import FastAPI

app = FastAPI(title="AI Course Research Platform", version="0.1.0")


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ok"}
