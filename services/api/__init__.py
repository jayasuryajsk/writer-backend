from fastapi import FastAPI

app = FastAPI()

from . import auth_google  # noqa: E402,F401
app.include_router(auth_google.router)
