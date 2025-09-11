from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict, deque
from threading import Lock

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
from app.routes import pti
from app.routes import onboarding
from app.routes import sharing
from app.routes import subscriptions
from app.routes import messages
from app.routes import accountability
from app.routes import analytics
from app.routes import csv_import

app = FastAPI(
    title="NestCash API",
    description="Personal Finance Management API with Knowledge Base",
    version="1.0.0"
)

# Rate limiting storage
rate_limit_storage = defaultdict(deque)
rate_limit_lock = Lock()

def is_rate_limited(client_ip: str, limit: int = 100, window: int = 60):
    """Ellenőrzi, hogy az IP túllépte-e a rate limitet"""
    current_time = time.time()
    
    with rate_limit_lock:
        # Régi bejegyzések törlése
        while (rate_limit_storage[client_ip] and 
               current_time - rate_limit_storage[client_ip][0] > window):
            rate_limit_storage[client_ip].popleft()
        
        # Jelenlegi kérés számának ellenőrzése
        if len(rate_limit_storage[client_ip]) >= limit:
            return True
        
        # Új kérés hozzáadása
        rate_limit_storage[client_ip].append(current_time)
        return False

# CORS middleware hozzáadása
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Fejlesztésben, production-ben korlátozni kell
    allow_credentials=False,
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
app.include_router(pti.router)
app.include_router(onboarding.router)
app.include_router(sharing.router)
app.include_router(subscriptions.router)
app.include_router(messages.router)
app.include_router(accountability.router)
app.include_router(analytics.router)
app.include_router(csv_import.router)

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
            "Habit Tracking",
            "PTI System",
            "Onboarding",
            "CSV Import",
        ]
    }

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Rate limit ellenőrzése (100 kérés/perc)
    if is_rate_limited(client_ip, limit=100, window=60):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded", 
                "message": "Too many requests. Try again later.",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Render.com automatikusan beállítja a PORT környezeti változót
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Fontos: 0.0.0.0 nem localhost!
        port=port,
        reload=False  # Production-ben ne legyen reload
    )