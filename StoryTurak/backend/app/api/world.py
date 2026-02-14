from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel
from app.services.content_service import get_all_zones, get_zone_encounters
import sys

router = APIRouter(prefix="/world", tags=["world"])

class Zone(BaseModel):
    id: str
    name: str
    description: str
    boundary_points: List[List[float]]
    difficulty_level: int

class Encounter(BaseModel):
    id: str
    title: str
    description: str
    type: str # quest, random, story
    nodes: dict
    start_node_id: str
    location: List[float]
    zone_id: str

@router.get("/nearby")
def get_nearby_world(lat: float, lon: float):
    sys.stderr.write(f"🌍🌍🌍 get_nearby_world called! lat={lat}, lon={lon}\n")
    sys.stderr.flush()
    # Fetch from Database via Content Service logic
    # Note: In a real app, we would pass lat/lon to filter the SQL query.
    
    # Collect encounters and zone details
    from app.db.crud import get_zone_control
    
    zones = get_all_zones()
    enriched_zones = []
    
    for z in zones:
        # Fetch Control Data
        zc = get_zone_control(z["id"])
        if zc:
            z["controlling_faction"] = zc["controlling_faction"]
        else:
            z["controlling_faction"] = "none" # Default
            
        enriched_zones.append(z)
    
    encounters = []
    for z in zones:
        zone_encs = get_zone_encounters(z["id"])
        encounters.extend(zone_encs)
        
    # Also include Tutorial Encounters (dynamic zone)
    sys.stderr.write("🎯🎯🎯 About to fetch zone_tutorial encounters...\n")
    sys.stderr.flush()
    tutorial_encs = get_zone_encounters("zone_tutorial")
    sys.stderr.write(f"🎯🎯🎯 Got {len(tutorial_encs)} tutorial encounters\n")
    sys.stderr.flush()
    encounters.extend(tutorial_encs)
    
    sys.stderr.write(f"✅✅✅ Returning {len(encounters)} total encounters\n")
    sys.stderr.flush()
    return {"zones": enriched_zones, "encounters": encounters}
