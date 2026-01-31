import random
from app.models.schemas import Character, Item, ItemType, EncounterNode, ItemEffectType

STANCE_MATRIX = {
    "strength": "tactics", # Rock beats Scissors
    "agility": "strength", # Paper beats Rock
    "tactics": "agility"   # Scissors beats Paper
}

class CombatService:
    @staticmethod
    def calculate_combat_round(character: Character, enemy_stance: str, player_stance: str, enemy_power: int = 1):
        """
        Resolves a single round of combat.
        """
        # 1. Calculate Effective Stats (Base + Items)
        effective_stats = character.stats.copy() if character.stats else {"strength": 1, "agility": 1, "tactics": 1}
        crit_chance = 0.0
        
        # Apply Item Effects
        # Note: In a real scenario, we'd ensure 'inventory' items are full Item objects or joined
        for slot in character.inventory:
            # CHECK EQUIPPED STATUS
            is_equipped = False
            if hasattr(slot, "equipped"): is_equipped = slot.equipped
            elif isinstance(slot, dict): is_equipped = slot.get("equipped", False)

            if not is_equipped:
                continue

            # We skip parsing complex logic for now and assume slot might have 'effects' if enriched
            # For this MVP, we rely on the fact that get_characters enrichment includes 'effects'
            # If slot is InventorySlot, it has 'effects' field (list of Any/Dict)
            if hasattr(slot, "effects") and slot.effects:
                for eff in slot.effects:
                    # eff can be dict or ItemEffect object
                    eff_type = eff.get("type") if isinstance(eff, dict) else eff.type
                    eff_val = eff.get("value") if isinstance(eff, dict) else eff.value
                    eff_target = eff.get("target_stat") if isinstance(eff, dict) else eff.target_stat
                    
                    if eff_type == "stat_bonus" and eff_target in effective_stats:
                        effective_stats[eff_target] += int(eff_val)
                    elif eff_type == "combat_crit" and player_stance == "agility": # Special rule: Crits mostly trigger on Agility/Csel
                        crit_chance += eff_val

        # 2. Base Resolution (RPS)
        result = "draw"
        if STANCE_MATRIX[player_stance] == enemy_stance:
            result = "win"
        elif STANCE_MATRIX[enemy_stance] == player_stance:
            result = "lose"
            
        # 3. Apply Modifiers
        player_power = effective_stats.get(player_stance, 1)
        
        # Logic: 
        # Win = Base Win OR (Draw AND Higher Power)
        # Lose = Base Lose OR (Draw AND Lower Power)
        
        final_result = result
        damage_dealt = 0
        damage_taken = 0
        
        if result == "win":
            # Critical Hit Check
            is_crit = random.random() < crit_chance
            mult = 2.0 if is_crit else 1.0
            damage_dealt = int(player_power * mult)
        elif result == "lose":
            damage_taken = max(1, enemy_power) 
            # Defense Stance mitigation could go here
            if player_stance == "tactics":
                damage_taken = max(0, damage_taken - (player_power // 2))
        else: # Draw
            if player_power > enemy_power:
                final_result = "win"
                damage_dealt = player_power - enemy_power
            elif enemy_power > player_power:
                final_result = "lose"
                damage_taken = enemy_power - player_power

        return {
            "result": final_result,
            "player_stance": player_stance,
            "enemy_stance": enemy_stance,
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,
            "player_power": player_power,
            "enemy_power": enemy_power,
            "flavor_text": CombatService._generate_flavor_text(final_result, player_stance, enemy_stance, damage_dealt, damage_taken)
        }

    @staticmethod
    def _generate_flavor_text(result, p_stance, e_stance, d_dealt, d_taken):
        if result == "win":
            return f"Győzelem! A {p_stance} legyőzte a {e_stance}-t. (Sebzés: {d_dealt})"
        elif result == "lose":
            return f"Vereség! Az ellenfél {e_stance}-e túl erős volt. (Sérülés: {d_taken})"
        return f"Döntetlen! A két {p_stance} egymásnak feszült."
