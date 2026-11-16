from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.reviews.router import router as reviews_router

app = FastAPI(title="LLM Code Reviewer")
app.include_router(auth_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
