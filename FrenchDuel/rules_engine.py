from cards import Card, is_figure_or_ace

class RulesEngine:
    """
    Handles the core game logic for damage calculation, special rules,
    bonuses, and checking for serious injuries/elimination.
    """
    def __init__(self):
        pass

    def calculate_round_outcome(self, attacker_card: Card, defender_card: Card):
        """
        Calculates the raw damage and checks for special rule effects.
        Returns: (initial_damage_before_bonuses, serious_injury_to_attacker, two_vs_figure_bonus_applied)
        initial_damage_before_bonuses: int, can be 0 or positive. This is the damage before combo/number bonuses.
        serious_injury_to_attacker: bool, True if attacker suffers a serious injury.
        two_vs_figure_bonus_applied: int, 6 if special rule 2 (attacker 2 vs defender figure/ace) applies, else 0.
        """
        initial_damage_before_bonuses = 0
        serious_injury_to_attacker = False
        two_vs_figure_bonus_applied = 0 # Specifically for the +6 damage rule

        attacker_score = attacker_card.get_score_value()
        defender_score = defender_card.get_score_value()

        # Apply special rules first
        # Rule 1: Attacker plays Figure/Ace, Defender plays 2 or 3
        if is_figure_or_ace(attacker_card) and defender_card.value in [2, 3]:
            serious_injury_to_attacker = True
            print(f"  SPECIAL RULE: {attacker_card} (Attacker) vs {defender_card} (Defender) -> Attacker suffers serious injury!")
            return 0, serious_injury_to_attacker, 0 # No damage, attacker injured

        # Rule 2: Defender plays Figure/Ace
        if is_figure_or_ace(defender_card):
            if attacker_card.value == 2:
                initial_damage_before_bonuses = 6 # This is the +6 damage
                two_vs_figure_bonus_applied = 6
                print(f"  SPECIAL RULE: {attacker_card} (Attacker) vs {defender_card} (Defender) -> Attacker deals +6 damage!")
                return initial_damage_before_bonuses, False, two_vs_figure_bonus_applied
            elif attacker_card.value == 3:
                print(f"  SPECIAL RULE: {attacker_card} (Attacker) vs {defender_card} (Defender) -> No damage, no injury.")
                return 0, False, 0 # No damage, no injury
            # If defender plays figure/ace and attacker doesn't play 2 or 3,
            # the normal damage calculation applies, handled below.

        # Normal damage calculation if no special rule above resulted in early return
        raw_damage = attacker_score - defender_score
        if raw_damage > 0:
            initial_damage_before_bonuses = raw_damage
        elif raw_damage < 0:
            serious_injury_to_attacker = True
        # If raw_damage is 0, initial_damage_before_bonuses remains 0, serious_injury_to_attacker remains False

        return initial_damage_before_bonuses, serious_injury_to_attacker, two_vs_figure_bonus_applied

    def check_phase_end(self, attacker_serious_injuries, rounds_played):
        """
        Checks if the current duel phase should end.
        """
        if attacker_serious_injuries >= 3:
            return True
        if rounds_played >= 6:
            return True
        return False

    def apply_bonuses(self, attacker_card_history: list[Card], attacker_card: Card, initial_damage: int, serious_injury_occurred: bool, two_vs_figure_bonus_applied: int):
        """
        Applies bonus damage based on consecutive card plays and winning cards.
        Returns a dictionary with breakdown of damage sources.
        """
        # Initialize all bonus components to 0
        base_hit_damage = 0
        suit_bonus = 0
        color_group_bonus = 0
        range_5_8_bonus = 0
        nine_multiplier_bonus = 0 # This will be the multiplied amount, not just the multiplier
        
        final_damage = initial_damage # Start with the damage from calculate_round_outcome

        # If a serious injury occurred, no damage is dealt, and no bonuses apply.
        if serious_injury_occurred:
            return {
                'final_damage': 0,
                'base_hit_damage': 0,
                'suit_bonus': 0,
                'color_group_bonus': 0,
                'range_5_8_bonus': 0,
                'nine_multiplier_bonus': 0,
                'two_vs_figure_bonus': 0,
                'total_bonus_damage': 0
            }

        # Calculate base hit damage (excluding the special +6 from 2 vs figure)
        # This represents the damage from (Attacker_score - Defender_score) if positive.
        base_hit_damage = initial_damage - two_vs_figure_bonus_applied

        # Apply winning card bonuses ONLY if there was a positive initial damage
        # (meaning the attacker won the base comparison, or the 2 vs figure rule applied)
        if initial_damage > 0:
            # Rule: 5-8-as lappal nyert ütés +2 sebzés
            if attacker_card.value in [5, 6, 7, 8]:
                print(f"  Bonus: Winning with a card from 5-8 range gives +2 damage.")
                range_5_8_bonus = 2
                final_damage += range_5_8_bonus

            # Rule: 9-essel nyert ütés esetén a sebzés duplázódik
            if attacker_card.value == 9:
                print(f"  Bonus: Winning with a 9 doubles the damage.")
                # The 9-multiplier applies to the damage accumulated so far (base + 2_vs_figure + 5_8_bonus)
                # To calculate the 'bonus' from doubling, we find the current total and subtract it from the doubled total.
                damage_before_nine_double = final_damage # This is initial_damage + range_5_8_bonus
                final_damage *= 2
                nine_multiplier_bonus = final_damage - damage_before_nine_double
        
        # Combo bonuses (applied if initial_damage > 0)
        # These bonuses are added to the final_damage AFTER the number-based bonuses and doubling.
        combo_base_damage = 0
        if initial_damage > 0: # Combo bonuses also only apply on a winning hit
            if len(attacker_card_history) >= 2:
                last_card = attacker_card_history[-1] # This is the current attacker_card
                second_last_card = attacker_card_history[-2]

                # Színbónusz: 2 egymás utáni azonos színű lap
                if last_card.suit == second_last_card.suit:
                    combo_base_damage += 3
                    suit_bonus = 3
                    print(f"  Combo Bonus: Same suit bonus (+3 base damage).")

                # Színcsoport-sorozat: 2 egymás utáni azonos színcsoport
                if last_card.color_group == second_last_card.color_group:
                    combo_base_damage += 1
                    color_group_bonus = 1
                    print(f"  Combo Bonus: Same color group bonus (+1 base damage).")

            if len(attacker_card_history) >= 3:
                last_card = attacker_card_history[-1]
                second_last_card = attacker_card_history[-2]
                third_last_card = attacker_card_history[-3]

                # Színcsoport-sorozat: 3 egymás utáni azonos színcsoport
                if last_card.color_group == second_last_card.color_group and \
                   second_last_card.color_group == third_last_card.color_group:
                    # Adjust for the +1 already added by 2-card combo, add +2 for 3-card combo
                    combo_base_damage -= 1 # Remove the previous +1
                    combo_base_damage += 2 # Add the +2 for the 3-card combo
                    color_group_bonus = 2 # Update to 2 for the 3-card combo
                    print(f"  Combo Bonus: Same color group streak (+2 base damage).")

            if combo_base_damage > 0:
                final_combo_bonus = combo_base_damage * 2 # Combo bonuses are doubled if the attacker wins
                print(f"  Combo bonuses applied: {combo_base_damage} base, 2x multiplier -> total {final_combo_bonus} bonus damage.")
                final_damage += final_combo_bonus
                suit_bonus *= 2 # Double the component for reporting
                color_group_bonus *= 2 # Double the component for reporting

        total_bonus_damage = suit_bonus + color_group_bonus + range_5_8_bonus + nine_multiplier_bonus + two_vs_figure_bonus_applied

        return {
            'final_damage': final_damage,
            'base_hit_damage': base_hit_damage,
            'suit_bonus': suit_bonus,
            'color_group_bonus': color_group_bonus,
            'range_5_8_bonus': range_5_8_bonus,
            'nine_multiplier_bonus': nine_multiplier_bonus,
            'two_vs_figure_bonus': two_vs_figure_bonus_applied,
            'total_bonus_damage': total_bonus_damage # Sum of all specific bonuses
        }
