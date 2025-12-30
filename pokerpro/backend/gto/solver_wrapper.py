import sys
import os
from typing import Dict, Any, List, Optional
import logging

# Add the quickgto_repo directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
quickgto_path = os.path.join(current_dir, 'quickgto_repo')
if quickgto_path not in sys.path:
    sys.path.append(quickgto_path)

try:
    from backend.gto.quickgto_repo import gto_helper
except ImportError:
    # If package import fails, try direct path import or fail gracefully
    try:
        import gto_helper
    except ImportError:
        gto_helper = None
        logging.warning("QuickGTO (gto_helper) could not be imported. Solver features will be disabled.")

class GTOSolver:
    """Abstract base class/interface for GTO solvers"""
    
    def solve(self, hero_hand: str, board: str, villains: int = 1, potter_settings: Dict = None) -> Dict[str, Any]:
        raise NotImplementedError

class QuickGTOSolver(GTOSolver):
    """Wrapper for the QuickGTO (sol5000) solver"""
    
    def __init__(self):
        if not gto_helper:
            raise RuntimeError("QuickGTO module not found")
            
    def solve(self, hero_hand: str, board: str, villains: int = 2, iterations: int = 10000, 
              pot: float = None, stack: float = None, facing_bet: float = None) -> Dict[str, Any]:
        """
        Solve a spot using QuickGTO (gto_helper).
        """
        # Parse inputs using gto_helper utilities
        try:
            h_cards = gto_helper.cards(hero_hand)
            b_cards = gto_helper.cards(board)
        except Exception as e:
            return {"error": f"Invalid card input: {str(e)}"}
            
        # Run equity simulation
        eq, hist = gto_helper.equity(h_cards, b_cards, villains, iters=iterations, game="Holdem")

        # Determine strategy/action
        evs = {}
        strategy = {"FOLD": 0.0, "CHECK": 0.0, "BET": 0.0}
        
        if pot is not None and facing_bet is not None:
            # Enhanced mode with EV
            stack_val = stack if stack is not None else 100.0
            
            # Calculate generic strategy
            # We use '1' (Pot sized) as the reference for the "Recommended Action" text
            ref_act, fold_ev, call_ev, ref_raise_ev, _ = gto_helper.decide_bets(eq, pot, facing_bet, stack_val, "1")
            best_action = ref_act
            
            # Populate EVs for multiple sizes
            evs = {
                "FOLD": fold_ev,
            }
            
            is_check_possible = (facing_bet == 0)
            if is_check_possible:
                evs["CHECK"] = call_ev
            else:
                evs["CALL"] = call_ev

            # Bet sizes
            for size_name, size_key in [("SMALL", "0.5"), ("POT", "1"), ("BIG", "2"), ("ALLIN", "shove")]:
                 _, _, _, r_ev, _ = gto_helper.decide_bets(eq, pot, facing_bet, stack_val, size_key)
                 action_label = f"RAISE_{size_name}" if facing_bet > 0 else f"BET_{size_name}"
                 evs[action_label] = r_ev
                 
            # If Best Action is generic 'RAISE'/'BET', refine it to the specific best size
            if best_action in ['RAISE', 'BET', 'ALL_IN']:
                # Find max EV among bet/raise options
                bet_evs = {k: v for k, v in evs.items() if 'BET' in k or 'RAISE' in k or 'ALLIN' in k}
                best_size_action = max(bet_evs, key=bet_evs.get)
                
                # Update recommended action clearly
                best_action = best_size_action
                strategy['BET'] = 1.0 # Keep strategy graph generic
                
            elif best_action == 'FOLD':
                strategy['FOLD'] = 1.0
            elif best_action in ['CHECK', 'CALL']:
                strategy['CHECK'] = 1.0

        else:
            # Simple mode (Equity only fallback)
            best_action = gto_helper.strict_action(eq)
            strategy = {"FOLD": 0.0, "CHECK": 0.0, "BET": 0.0}
            
            # Strict action mapping
            if best_action == 'RAISE': strategy['BET'] = 1.0
            elif best_action == 'CHECK': strategy['CHECK'] = 1.0
            elif best_action == 'FOLD': strategy['FOLD'] = 1.0
            
            # Dummy EV
            evs = {
                "FOLD": 0.0,
                "CHECK": eq * 10.0,
                "BET": eq * 10.0 + 2.0
            }

        # Generate explanation
        explanation = self.explain_result(eq, best_action)

        return {
            "equity": eq,
            "strategy": strategy,
            "evs": evs,
            "recommended_action": best_action,
            "details": {
                "equity_histogram": hist.tolist() if hasattr(hist, "tolist") else hist
            },
            "explanation": explanation
        }
    
            
    def explain_result(self, equity: float, action: str) -> str:
        """Generate a natural language explanation for the GTO decision."""
        pct = equity * 100
        
        # Base explanation on Equity
        if pct >= 80:
            base = f"With massive equity ({pct:.1f}%), you have a nut-strength hand."
            reason = "You should be betting for pure value to build the pot against weaker hands."
        elif pct >= 65:
            base = f"You have strong equity ({pct:.1f}%) here."
            reason = "A value bet is profitable, but be cautious of check-raises on dangerous boards."
        elif pct >= 50:
            base = f"This is a marginal spot with {pct:.1f}% equity."
            reason = "You are flipping against their range. Pot control (checking) is often good, or a small probe bet."
        elif pct >= 35:
            base = f"You are likely behind ({pct:.1f}% equity), but have some outs."
            reason = "Checking is standard. If you bet, it's a semi-bluff relying on fold equity."
        else:
            base = f"You have very low equity ({pct:.1f}%)."
            reason = "You are bluff-catching at best. Checking or Folding is standard unless you have specific reads."

        # Adjust based on Action
        if action == "RAISE" or action == "BET":
            advice = "The solver prefers aggression here to capitalize on your advantage."
        elif action == "CHECK":
            advice = "The solver prefers passivity to realize equity or give up cheaply."
        else:
            advice = "The solver recommends folding to save chips."

        return f"{base} {advice} {reason}"

def get_solver(name: str = "quickgto") -> GTOSolver:
    if name == "quickgto":
        return QuickGTOSolver()
    raise ValueError(f"Unknown solver: {name}")
