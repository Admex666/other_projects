from fastapi import FastAPI

from app.core.db import init_db
from app.routes import auth
from app.routes import transactions
from app.routes import accounts
from app.routes import categories
from app.routes import analysis

app = FastAPI()
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(analysis.router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "NestCash API works!"}

