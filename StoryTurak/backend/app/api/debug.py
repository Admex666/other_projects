from fastapi import APIRouter
from app.services.content_service import get_zone_encounters

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/tutorial-encounters")
def get_tutorial_encounters():
    """Direct test endpoint to check tutorial encounters"""
    print("🧪 DEBUG: Fetching tutorial encounters...", flush=True)
    encounters = get_zone_encounters("zone_tutorial")
    print(f"🧪 DEBUG: Found {len(encounters)} encounters", flush=True)
    return {
        "count": len(encounters),
        "encounters": encounters
    }
