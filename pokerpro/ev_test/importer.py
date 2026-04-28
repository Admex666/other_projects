import json
import random
import re

def parse_pokerbench(input_file, output_file, num_spots=20):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Shuffle to get a good mix
    random.seed(42)
    random.shuffle(data)
    
    new_spots = []
    
    for item in data[:num_spots]:
        instr = item['instruction']
        output = item['output']
        
        # Extract situation summary
        # We look for the part after "Here is a game summary:"
        summary_match = re.search(r"In this hand, your position is (.*?)Decide on an action", instr, re.DOTALL)
        if summary_match:
            situation_text = summary_match.group(1).strip()
            # Clean up the text a bit
            situation_text = situation_text.replace("\n", " ").replace("  ", " ")
        else:
            situation_text = "Detailed poker scenario from PokerBench."

        # Extract hand
        hand_match = re.search(r"your holding is \[(.*?)\]", instr)
        hand = hand_match.group(1) if hand_match else "Unknown"

        # Extract Pot Size
        pot_match = re.search(r"current pot size is ([\d.]+) chips", instr)
        pot_size = float(pot_match.group(1)) if pot_match else 10.0

        # Generate options
        correct_action = output
        # Heuristic: a mistake costs roughly 10% of the pot in EV on average
        optimal_ev = pot_size * 0.5 # Arbitrary baseline
        wrong_ev = optimal_ev - (pot_size * 0.15) # 15% pot loss for a mistake

        # Simple heuristic for wrong actions
        wrong_actions = []
        if "check" in correct_action.lower():
            wrong_actions = ["bet 1/2 pot", "fold"]
        elif "call" in correct_action.lower():
            wrong_actions = ["fold", "raise 3x"]
        elif "bet" in correct_action.lower() or "raise" in correct_action.lower():
            wrong_actions = ["check", "fold"]
        elif "fold" in correct_action.lower():
            wrong_actions = ["call", "raise 3x"]
        else:
            wrong_actions = ["check", "call"]

        options = [{"action": correct_action, "ev": optimal_ev, "description": "Optimal GTO decision according to PokerBench."}]
        for wa in list(set(wrong_actions))[:2]:
            options.append({"action": wa, "ev": wrong_ev, "description": "Suboptimal move."})
        
        # Shuffle options
        random.shuffle(options)

        new_spots.append({
            "id": len(new_spots) + 1,
            "situation": situation_text,
            "hand": hand,
            "options": options,
            "optimal_action": correct_action,
            "source": "PokerBench (Objective GTO Dataset)",
            "pot_size": pot_size
        })


    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_spots, f, indent=4)
    
    print(f"Successfully imported {len(new_spots)} spots from PokerBench.")

if __name__ == "__main__":
    parse_pokerbench('pokerbench_postflop.json', 'spots.json', num_spots=10)
