
import random
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel
import eval7
from . import preflop_ranges
from .quickgto_repo import gto_helper

class DrillScenario(BaseModel):
    hero_hand: str
    board: str
    villains: int
    pot: float
    stack: float
    facing_bet: float
    description: str

class DrillManager:
    @staticmethod
    def _sample_hand_from_range(range_dict: Dict[str, float], exclude_cards: List[eval7.Card] = []) -> str:
        """Weighted sampling of a specific hand combo from a range dict"""
        # Expand range dict (e.g. "AKs": 1.0) into specific combos (e.g. "AhKh")
        weighted_combos = []
        
        # Rankings for expansion
        RANKS = "AKQJT98765432"
        SUITS = "shdc"
        
        exclude_strs = [str(c) for c in exclude_cards]
        
        for hand_type, freq in range_dict.items():
            if freq <= 0: continue
            
            combos = []
            if len(hand_type) == 2: # Pair (AA)
                r = hand_type[0]
                # Generate 6 pairs
                for i in range(4):
                    for j in range(i + 1, 4):
                        c1 = r + SUITS[i]
                        c2 = r + SUITS[j]
                        if c1 not in exclude_strs and c2 not in exclude_strs:
                            combos.append(c1 + c2)
                            
            elif hand_type.endswith('s'): # Suited (AKs)
                r1, r2 = hand_type[0], hand_type[1]
                # Generate 4 suited
                for s in SUITS:
                    c1 = r1 + s
                    c2 = r2 + s
                    if c1 not in exclude_strs and c2 not in exclude_strs:
                        combos.append(c1 + c2)
            
            elif hand_type.endswith('o'): # Offsuit (AKo)
                r1, r2 = hand_type[0], hand_type[1]
                # Generate 12 offsuit
                for s1 in SUITS:
                    for s2 in SUITS:
                        if s1 == s2: continue
                        c1 = r1 + s1
                        c2 = r2 + s2
                        if c1 not in exclude_strs and c2 not in exclude_strs:
                            combos.append(c1 + c2)
            
            # Add to pool with weight
            for c in combos:
                weighted_combos.append((c, freq))
                
        # Sample
        if not weighted_combos:
            return "AhAs" # Fallback
            
        total_weight = sum(w for c, w in weighted_combos)
        r = random.uniform(0, total_weight)
        current = 0
        for combo, w in weighted_combos:
            current += w
            if r <= current:
                return combo
        
        return weighted_combos[0][0]

    @staticmethod
    def generate_drill(drill_type: str) -> DrillScenario:
        # 1. Setup Deck
        deck = eval7.Deck()
        deck.shuffle()
        used_cards = []
        
        hero_hand_str = ""
        hero_range = {}
        villain_range = {}
        pot = 0.0
        desc = ""
        
        # 2. Configure Scenarios
        if drill_type == "btn_vs_bb_srp":
            desc = "BTN Open vs BB Call (Single Raised Pot)"
            hero_range = preflop_ranges.get_rfi_range("BTN")
            # Sample Hero Hand
            hero_hand_str = DrillManager._sample_hand_from_range(hero_range, [])
            
            # Sample Villain Hand (Virtual - just to simulate card removal if we wanted, 
            # but for now we just need to ensure board doesn't clash)
            # We don't strictly need to pick a villain hand for the solver, 
            # the solver will assume villain has the full range (which we should arguably pass to it, 
            # but QuickGTO mostly assumes generic ranges or we pass % range).
            # For this simple implementation, we just make sure Hero hand is valid.
            
            pot = 4.5 # 2.5x open + 1bb + 0.5bb
            
        elif drill_type == "sb_vs_bb_limp":
            desc = "SB Limp vs BB Check"
            hero_range = preflop_ranges.get_defend_range("BB", "BTN") # Reuse wide range for SB limp
            hero_hand_str = DrillManager._sample_hand_from_range(hero_range, [])
            pot = 2.0
            
        elif drill_type == "3bet_pot_oop": # SB/BB 3bet vs BTN
            desc = "3-Bet Pot (Out of Position)"
            hero_range = preflop_ranges.get_3bet_range("SB", "BTN")
            hero_hand_str = DrillManager._sample_hand_from_range(hero_range, [])
            pot = 20.0 # ~9bb 3bet + 3bb call
            
        else: # Random Fallback (High Card random)
            desc = "Random Scenario"
            h1 = deck.deal(1)[0]
            h2 = deck.deal(1)[0]
            hero_hand_str = str(h1) + str(h2)
            pot = 10.0
            
        # 3. Deal Board
        # Extract hero cards to remove from deck
        h_cards = gto_helper.cards(hero_hand_str)
        
        # Re-create deck without hero cards
        deck = eval7.Deck()
        for c in h_cards:
            deck.cards.remove(c)
        deck.shuffle()
        
        # Random street (Flop 40%, Turn 30%, River 30%)
        r = random.random()
        num_board = 3 if r < 0.4 else (4 if r < 0.7 else 5)
        
        board_cards = deck.deal(num_board)
        board_str = "".join([str(c) for c in board_cards])
        
        # 4. Facing Bet Simulation
        # Simple logic: 50% check, 50% bet faced
        facing = 0.0
        if random.random() > 0.6:
            # Face a bet of 33-75% pot
            bet_pct = random.choice([0.33, 0.5, 0.75])
            facing = round(pot * bet_pct, 1)
            
        return DrillScenario(
            hero_hand=hero_hand_str,
            board=board_str,
            villains=2,
            pot=pot,
            stack=95.0, # Remaining stack
            facing_bet=facing,
            description=desc
        )
