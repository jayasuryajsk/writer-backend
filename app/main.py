from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/login")
async def login():
    # Placeholder login endpoint
    return {"token": "dummy"}
