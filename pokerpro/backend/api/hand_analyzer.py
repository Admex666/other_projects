from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.user import User
from models.hands import HandHistory, HandAnalysis
from schemas.hands import HandImport, HandAnalysisResponse, LeakDetection
from api.auth import get_current_user
from hand_parser.parser import parse_hand_history

router = APIRouter()


def analyze_hand(parsed_hand: dict) -> dict:
    """
    Analyze a parsed hand for leaks and mistakes
    
    This is a simplified version. In production, this would use ML models
    and more sophisticated GTO comparisons.
    """
    
    leaks = []
    overall_score = 85.0  # Default good score
    ev_loss = 0.0
    
    # Example leak detection (simplified)
    # In reality, this would analyze each action against GTO
    
    # Sample leak
    leaks.append({
        "street": "flop",
        "action": "call",
        "leak_type": "overcalling",
        "ev_loss": 0.3,
        "explanation": "This call is slightly -EV. Consider folding more often in this spot."
    })
    
    recommendations = """
    **Preflop:** Your open-raise sizing was good.
    
    **Flop:** Consider checking back more often with this hand strength on this board texture.
    
    **Turn:** Good value bet sizing.
    
    **Overall:** Solid play with minor adjustments needed.
    """
    
    return {
        "overall_score": overall_score,
        "ev_loss": ev_loss,
        "leaks": leaks,
        "gto_comparison": {
            "preflop": {"action": "raise", "gto_action": "raise", "ev_diff": 0.0},
            "flop": {"action": "call", "gto_action": "fold", "ev_diff": -0.3}
        },
        "recommendations": recommendations
    }


@router.post("/import")
async def import_hand(
    hand_data: HandImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a hand history for analysis"""
    
    # Parse hand
    parsed = parse_hand_history(hand_data.raw_hand_text, hand_data.site)
    
    if not parsed.get("hand_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse hand history"
        )
    
    # Check if hand already exists
    existing = db.query(HandHistory).filter(
        HandHistory.hand_id == parsed["hand_id"],
        HandHistory.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hand already imported"
        )
    
    # Create hand history record
    hand = HandHistory(
        user_id=current_user.id,
        hand_id=parsed["hand_id"],
        site=parsed["site"],
        game_type=parsed["game_type"],
        stakes=parsed["stakes"],
        raw_hand_text=hand_data.raw_hand_text,
        parsed_data=parsed
    )
    
    db.add(hand)
    db.commit()
    db.refresh(hand)
    
    return {
        "success": True,
        "hand_id": hand.hand_id,
        "message": "Hand imported successfully"
    }


@router.get("/analyze/{hand_id}", response_model=HandAnalysisResponse)
async def analyze_hand_endpoint(
    hand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze an imported hand"""
    
    # Get hand
    hand = db.query(HandHistory).filter(
        HandHistory.hand_id == hand_id,
        HandHistory.user_id == current_user.id
    ).first()
    
    if not hand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found"
        )
    
    # Check if already analyzed
    existing_analysis = db.query(HandAnalysis).filter(
        HandAnalysis.hand_id == hand.id
    ).first()
    
    if existing_analysis:
        return HandAnalysisResponse(
            hand_id=hand.hand_id,
            overall_score=existing_analysis.overall_score,
            ev_loss=existing_analysis.ev_loss,
            leaks=[LeakDetection(**leak) for leak in existing_analysis.leaks],
            gto_comparison=existing_analysis.gto_comparison,
            recommendations=existing_analysis.recommendations,
            analyzed_at=existing_analysis.analyzed_at
        )
    
    # Analyze hand
    analysis_result = analyze_hand(hand.parsed_data)
    
    # Save analysis
    analysis = HandAnalysis(
        hand_id=hand.id,
        overall_score=analysis_result["overall_score"],
        ev_loss=analysis_result["ev_loss"],
        leaks=analysis_result["leaks"],
        gto_comparison=analysis_result["gto_comparison"],
        recommendations=analysis_result["recommendations"]
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return HandAnalysisResponse(
        hand_id=hand.hand_id,
        overall_score=analysis.overall_score,
        ev_loss=analysis.ev_loss,
        leaks=[LeakDetection(**leak) for leak in analysis.leaks],
        gto_comparison=analysis.gto_comparison,
        recommendations=analysis.recommendations,
        analyzed_at=analysis.analyzed_at
    )


@router.get("/my-hands")
async def get_my_hands(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's imported hands"""
    
    hands = db.query(HandHistory).filter(
        HandHistory.user_id == current_user.id
    ).order_by(HandHistory.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(hands),
        "hands": [
            {
                "hand_id": h.hand_id,
                "site": h.site,
                "game_type": h.game_type,
                "stakes": h.stakes,
                "imported_at": h.created_at,
                "analyzed": h.analysis is not None
            }
            for h in hands
        ]
    }
