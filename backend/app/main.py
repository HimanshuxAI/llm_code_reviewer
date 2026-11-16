from fastapi import FastAPI

from app.auth.router import router as auth_router

app = FastAPI(title="LLM Code Reviewer")
app.include_router(auth_router, prefix="/api")
