
import sys
import os

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gto.solver_wrapper import get_solver

def main():
    print("Testing QuickGTO Solver Integration...")
    
    try:
        solver = get_solver("quickgto")
        print("Solver instance created.")
        
        # Test Case: Hero has Aces over Kings, Board is somewhat coordinated
        # Hero: AhAd (Pocket Aces)
        # Board: Ks Qs Jh (Potential Straight/Flush draws)
        # Villains: 1
        
        hero = "AhAd"
        board = "KsQsJh"
        
        print(f"Solving for Hero: {hero}, Board: {board}...")
        result = solver.solve(hero, board, villains=1, iterations=1000)
        
        print("\n--- Solver Result ---")
        print(f"Equity: {result['equity']}")
        print(f"Strategy: {result['strategy']}")
        print(f"Recommended Action: {result['recommended_action']}")
        print("---------------------")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
