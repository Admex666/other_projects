from typing import Optional
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.gto import GTOQuery, GTOResponse, RangeData
from api.auth import get_current_user
from gto.preflop_ranges import get_rfi_range, get_3bet_range, calculate_vpip, visualize_range
from gto.equity_calculator import calculate_equity, calculate_outs
from gto.solver_wrapper import get_solver
from gto.drill_manager import DrillManager, DrillScenario

router = APIRouter()

@router.get("/drill", response_model=DrillScenario)
async def get_drill_scenario(type: str = "btn_vs_bb_srp"):
    """Generate a specific drill scenario"""
    try:
        scenario = DrillManager.generate_drill(type)
        return scenario
    except Exception as e:
        # Fallback to random if error
        return DrillManager.generate_drill("random")


@router.post("/preflop", response_model=GTOResponse)
async def get_preflop_solution(
    query: GTOQuery,
    current_user: User = Depends(get_current_user)
):
    """Get GTO preflop solution for given position and action"""
    
    # Get appropriate range
    if query.action == "rfi":
        range_dict = get_rfi_range(query.position, query.stack_depth)
    elif query.action == "3bet":
        # For now, default vs CO
        range_dict = get_3bet_range(query.position, "CO")
    else:
        range_dict = {}
    
    # Calculate VPIP
    vpip = calculate_vpip(range_dict)
    
    # Visualize range (full grid)
    full_range = visualize_range(range_dict)
    
    # Count total combos
    total_combos = sum(
        (6 if len(h) == 2 else 4 if h.endswith('s') else 12) * freq
        for h, freq in range_dict.items()
    )
    
    range_data = RangeData(
        ranges=full_range,
        total_combos=int(total_combos),
        vpip=round(vpip, 1)
    )
    
    recommendations = {
        "suggested_action": query.action,
        "sizing": [2.5, 3.0] if query.action == "rfi" else [8.0, 10.0],
        "description": f"GTO {query.action} range from {query.position}",
        "vpip": f"{vpip:.1f}%"
    }
    
    return GTOResponse(
        query=query,
        range_data=range_data,
        recommendations=recommendations
    )


@router.post("/equity")
async def calculate_hand_equity(
    hero_hand: str,
    villain_hand: str = None,
    board: str = "",
    current_user: User = Depends(get_current_user)
):
    """Calculate hand equity using Monte Carlo simulation"""
    
    equity = calculate_equity(
        hero_hand=hero_hand,
        villain_hand=villain_hand,
        board=board,
        simulations=10000
    )
    
    outs = calculate_outs(hero_hand, board) if board else 0
    
    return {
        "hero_hand": hero_hand,
        "villain_hand": villain_hand or "random",
        "board": board or "preflop",
        "equity": equity,
        "outs": outs,
        "pot_odds_needed": round(100 - equity, 2)
    }


@router.get("/practice/scenario")
async def get_practice_scenario(
    difficulty: str = "beginner",
    current_user: User = Depends(get_current_user)
):
    """Get a practice scenario for GTO training"""
    
    scenarios = {
        "beginner": {
            "situation": "BTN vs BB, 100BB deep",
            "hero_position": "BTN",
            "villain_position": "BB",
            "action": "You are on the BTN. Action folds to you. What should you do with K♠ J♦?",
            "correct_action": "raise",
            "explanation": "KJo is a clear raise from the BTN. You should be raising ~45% of hands from this position.",
            "gto_frequency": 0.8
        },
        "intermediate": {
            "situation": "CO opens, BTN 3-bets, you are in CO",
            "hero_position": "CO",
            "villain_position": "BTN",
            "action": "You opened from CO with A♠ Q♦. BTN 3-bets to 9BB. What should you do?",
            "correct_action": "call",
            "explanation": "AQo is a mix between call and 4-bet. Against most opponents, calling is preferred to keep their bluffs in.",
            "gto_frequency": 0.7
        }
    }
    
    return scenarios.get(difficulty, scenarios["beginner"])


from pydantic import BaseModel

class SolveRequest(BaseModel):
    hero_hand: str
    board: str = ""
    villains: int = 2
    pot: Optional[float] = None
    stack: Optional[float] = None
    facing_bet: Optional[float] = None

@router.post("/solve")
async def solve_spot(
    request: SolveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run QuickGTO solver for a specific spot.
    """
    try:
        solver = get_solver("quickgto")
        # Run with fewer iterations for the API response speed
        # Solve
        result = solver.solve(
            hero_hand=request.hero_hand,
            board=request.board,
            villains=request.villains,
            pot=request.pot,
            stack=request.stack,
            facing_bet=request.facing_bet,
            iterations=2000
        )
        return result
    except Exception as e:
        return {"error": str(e)}
