from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import init_db
from app.routes import auth
from app.routes import transactions
from app.routes import accounts
from app.routes import categories
from app.routes import analysis
from app.routes import knowledge
from app.routes import knowledge_admin
from app.routes import random_data
from app.routes import forum_posts
from app.routes import forum_interactions
from app.routes import forum_follow
from app.routes import forum_notifications
from app.routes import forum_settings
from app.routes import notifications
from app.routes import limits
from app.routes import challenges
from app.routes import badges
from app.routes import badge_admin
from app.routes import habits

app = FastAPI(
    title="NestCash API",
    description="Personal Finance Management API with Knowledge Base",
    version="1.0.0"
)

# CORS middleware hozzáadása
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Fejlesztésben, production-ben korlátozni kell
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router-ek hozzáadása
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(analysis.router)
app.include_router(knowledge.router)
app.include_router(knowledge_admin.router)
app.include_router(random_data.router)
app.include_router(forum_posts.router)
app.include_router(forum_interactions.router)
app.include_router(forum_follow.router)
app.include_router(notifications.router) 
app.include_router(limits.router)
app.include_router(challenges.router)
app.include_router(badges.router)
app.include_router(badge_admin.router)
app.include_router(habits.router)

@app.on_event("startup")
async def startup_event():
    await init_db()

    # Badge rendszer inicializálása
    try:
        from app.services.badge_init import initialize_badge_system
        await initialize_badge_system()
    except Exception as e:
        print(f"Badge system initialization failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "NestCash API works!",
        "version": "1.0.0",
        "features": [
            "Authentication",
            "Financial Transactions",
            "Account Management", 
            "Categories",
            "Financial Analysis",
            "Knowledge Base",
            "Admin Panel",
            "Spending Limits",
            "Challenges",
            "Badge System",
            "Habit Tracking"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}