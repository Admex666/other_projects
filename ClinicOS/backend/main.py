from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.api import router

# Create DB tables if they don't exist (though generator should have done this)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClinicOS API", version="1.0")

# CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "ClinicOS Backend is operational"}
