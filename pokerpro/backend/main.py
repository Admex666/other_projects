from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api import auth, onboarding, academy, gto_engine, hand_analyzer

# Create FastAPI app
app = FastAPI(
    title="PokerPro API",
    description="Professional Poker Training Platform API",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "PokerPro API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # TODO: Add actual DB health check
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(academy.router, prefix="/api/academy", tags=["Academy"])
app.include_router(gto_engine.router, prefix="/api/gto", tags=["GTO Engine"])
app.include_router(hand_analyzer.router, prefix="/api/hands", tags=["Hand Analyzer"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
