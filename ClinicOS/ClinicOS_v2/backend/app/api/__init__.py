from fastapi import APIRouter
from app.api.endpoints import import_data, dashboard, retention, scenario, manager

router = APIRouter()

router.include_router(import_data.router, prefix="/import", tags=["Import"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(retention.router, prefix="/retention", tags=["Retention"])
router.include_router(scenario.router, prefix="/scenario", tags=["Scenario"])
router.include_router(manager.router, prefix="/manager", tags=["Manager"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}
