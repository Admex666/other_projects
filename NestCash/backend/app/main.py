from fastapi import FastAPI
from app.core.db import init_db
from app.routes import auth

app = FastAPI()
app.include_router(auth.router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "NestCash API works!"}

