from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.scenario_service import ScenarioService
from app.models.schemas import SimulationParams

router = APIRouter()

@router.post("/simulate")
async def simulate_scenario(params: SimulationParams, db: Session = Depends(get_db)):
    return ScenarioService.run_simulation(db, params)
