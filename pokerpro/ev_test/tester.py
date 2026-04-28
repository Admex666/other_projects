import json
import os
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title.center(56)}")
    print("="*60 + "\n")

def run_test():
    with open('spots.json', 'r', encoding='utf-8') as f:
        spots = json.load(f)

    results = []
    
    clear_screen()
    print_header("POKER EV THEORY TESTER")
    print(f"Total scenarios: {len(spots)}")
    print("Analyze each spot and choose the best action based on GTO theory.\n")
    input("Press Enter to start...")

    for i, spot in enumerate(spots):
        clear_screen()
        print_header(f"SCENARIO {i+1}/{len(spots)}")
        print(f"SITUATION: {spot['situation']}")
        print(f"HAND:      {spot['hand']}\n")
        
        print("OPTIONS:")
        for j, opt in enumerate(spot['options']):
            print(f"  [{j+1}] {opt['action']}")
        
        print("-" * 60)
        
        choice = -1
        while choice < 0 or choice >= len(spot['options']):
            try:
                choice_str = input("\nYour decision (number): ")
                choice = int(choice_str) - 1
            except ValueError:
                print("Please enter a valid number.")

        selected_opt = spot['options'][choice]
        max_ev = max(opt['ev'] for opt in spot['options'])
        ev_loss = max_ev - selected_opt['ev']
        
        results.append({
            "spot_id": spot['id'],
            "choice": selected_opt['action'],
            "choice_ev": selected_opt['ev'],
            "max_ev": max_ev,
            "ev_loss": ev_loss,
            "correct": selected_opt['action'] == spot['optimal_action']
        })
        
        print(f"\nResult: {'CORRECT! ✅' if results[-1]['correct'] else 'SUBOPTIMAL ❌'}")
        print(f"EV Loss: {ev_loss:.2f} bb")
        print(f"Explanation: {selected_opt['description']}")
        time.sleep(2)

    # Save results
    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    clear_screen()
    print_header("TEST COMPLETE")
    print("Results saved to results.json.")
    print("Run analyzer.py to see your statistical performance.")

if __name__ == "__main__":
    run_test()
