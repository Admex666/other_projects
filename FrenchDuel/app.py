from flask import Flask, render_template, jsonify, request, session
from player import BotPlayer
from match import Match
from strategy import RandomStrategy, GreedyHighestValueStrategy
from cards import Card, is_figure_or_ace
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Session-hoz szükséges

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Request must be JSON'}), 415
        
        # Session inicializálás ha még nincs
        if 'match_history' not in session:
            session['match_history'] = {
                'player_total_damage': 0,
                'bot_total_damage': 0,
                'player_total_injuries': 0,
                'bot_total_injuries': 0,
                'current_phase': 1,
                'phase_results': []
            }
        
        # Játékos és bot létrehozása
        player = BotPlayer("Játékos", RandomStrategy())
        bot = BotPlayer("Bot", GreedyHighestValueStrategy())
    
        # Új mérkőzés
        current_match = Match(player, bot)
        
        # Kezdő támadó beállítása - szakaszok váltakozása alapján
        match_history = session['match_history']
        current_phase = match_history['current_phase']
        
        # Páratlan szakaszban játékos támad, páros szakaszban bot
        starting_attacker = player.name if current_phase % 2 == 1 else bot.name
        current_match._assign_roles(starting_attacker)

        # Kártyák osztása
        current_match._draft_attack_cards()
        current_match._draft_defense_cards()

        # Bot védőkártyák sorrendjének meghatározása
        bot_defense_order = []
        if not player.is_attacker:
            bot_defense_order = []
        else:
            bot_defense_order = bot.defense_hand.cards.copy()
            random.shuffle(bot_defense_order)

        # Játékállapot mentése session-be
        session['match_state'] = {
            'player_attack_hand': [{'value': card.value, 'suit': card.suit} for card in player.attack_hand.cards],
            'player_defense_hand': [{'value': card.value, 'suit': card.suit} for card in player.defense_hand.cards],
            'bot_attack_hand': [{'value': card.value, 'suit': card.suit} for card in bot.attack_hand.cards],
            'bot_defense_hand': [{'value': card.value, 'suit': card.suit} for card in bot.defense_hand.cards],
            'player_damage': 0,  # Szakasz sebzés
            'bot_damage': 0,
            'player_injuries': 0,  # Szakasz sérülések
            'bot_injuries': 0,
            'attacker': current_match.attacker.name,
            'defender': current_match.defender.name,
            'rounds_played': 0,
            'bot_defense_order': [{'value': card.value, 'suit': card.suit} for card in bot_defense_order],
            'attacker_card_history': []  # Bónusz számításhoz
        }
        
        return jsonify({
            'status': 'ready',
            'player_attack_hand': [str(card) for card in player.attack_hand.cards],
            'player_defense_hand': [str(card) for card in player.defense_hand.cards],
            'is_attacker': player.is_attacker,
            'current_phase': current_phase,
            'match_history': match_history,
            'bot_defense_order': [str(card) for card in bot_defense_order] if not player.is_attacker else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# A calculate_outcome függvény módosítása bónuszokkal
def calculate_outcome_with_bonuses(is_player_attacker, attacker_card, defender_card, attacker_card_history):
    """
    Számítja az eredményt az összes bónusszal együtt
    """
    from rules_engine import RulesEngine
    rules_engine = RulesEngine()
    
    # Alap eredmény számítás
    initial_damage, injury, two_vs_figure_bonus = rules_engine.calculate_round_outcome(
        attacker_card, defender_card
    )
    
    # Bónuszok alkalmazása
    damage_breakdown = rules_engine.apply_bonuses(
        attacker_card_history, attacker_card, initial_damage, injury, two_vs_figure_bonus
    )
    
    # Speciális szabályok szöveges leírása
    special_text = None
    if injury:
        special_text = "Súlyos sérülés a támadónak!"
    elif two_vs_figure_bonus > 0:
        special_text = "Kettes figura/ász ellen: +6 sebzés!"
    elif attacker_card.value == 3 and defender_card.get_score_value() > 10:
        special_text = "Hármas neutralizál figura/ász ellen"
    elif attacker_card.value == 4 and initial_damage == 0:
        special_text = "Négyes neutralizálja a védő előnyét"
    
    return damage_breakdown['final_damage'], injury, special_text, damage_breakdown

@app.route('/play_round', methods=['POST'])
def play_round():
    match_state = session.get('match_state')
    if not match_state:
        return jsonify({'error': 'Nincs aktív játék'}), 400
    
    try:
        # Játékos lépése
        card_index = request.json.get('card_index')
        
        # Játékállapot betöltése
        player = BotPlayer("Játékos", RandomStrategy())
        bot = BotPlayer("Bot", GreedyHighestValueStrategy())
        
        # Kártyák visszaállítása
        player.attack_hand.cards = [Card(card['value'], card['suit']) for card in match_state['player_attack_hand']]
        player.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['player_defense_hand']]
        bot.attack_hand.cards = [Card(card['value'], card['suit']) for card in match_state['bot_attack_hand']]
        bot.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['bot_defense_hand']]
        
        # Játékos kártyájának kiválasztása
        selected_card = player.attack_hand.cards[card_index]
        player.attack_hand.remove_card(selected_card)
        
        # Bot lépése - SZEREPEK HELYES IMPLEMENTÁLÁSA
        if match_state['attacker'] == 'Játékos':
            # Játékos a Támadó, Bot a Védő
            # Bot (Védő) először teszi le a lapját az előre meghatározott sorrendből
            if not match_state.get('bot_defense_order') or len(match_state['bot_defense_order']) == 0:
                return jsonify({'error': 'Bot defense order is empty'}), 500
            
            bot_card_dict = match_state['bot_defense_order'].pop(0)
            bot_card = next(
                (card for card in bot.defense_hand.cards if card.value == bot_card_dict['value'] and card.suit == bot_card_dict['suit']),
                None
            )
            if bot_card:
                bot.defense_hand.remove_card(bot_card)
            else:
                return jsonify({'error': 'Bot defense card not found in hand'}), 500
            
            # Játékos (Támadó) reagál a bot lapjára
            defender_card = bot_card  # Bot a védő
            attacker_card = selected_card  # Játékos a támadó
        else:
            # Bot a Támadó, Játékos a Védő
            # Játékos (Védő) először teszi le a lapját
            if len(player.defense_hand.cards) == 0:
                return jsonify({'error': 'Player has no defense cards left'}), 500
            
            # Játékos védőkártyája (első a kézből - egyszerűsített)
            player_defense_card = player.defense_hand.cards[0]
            player.defense_hand.remove_card(player_defense_card)
            
            # Bot (Támadó) reagál
            attacker_card = bot_card  # Bot a támadó
            defender_card = player_defense_card  # Játékos a védő
        
        # Eredmény számítás - helyes paraméter sorrend
        damage, injury, special = calculate_outcome(
            match_state['attacker'] == 'Játékos',  # Ki a támadó
            attacker_card,  # Támadó lapja
            defender_card   # Védő lapja
        )

        # Sérülések és sebzések alkalmazása
        if match_state['attacker'] == 'Játékos':
            # Játékos támad
            if injury:
                match_state['player_injuries'] += 1  # Támadó sérül
            if damage > 0:
                match_state['bot_damage'] += damage  # Védő kap sebzést
        else:
            # Bot támad
            if injury:
                match_state['bot_injuries'] += 1     # Támadó sérül
            if damage > 0:
                match_state['player_damage'] += damage  # Védő kap sebzést
        
        match_state['rounds_played'] += 1
        match_state['player_attack_hand'] = [card.__dict__ for card in player.attack_hand.cards]
        match_state['player_defense_hand'] = [card.__dict__ for card in player.defense_hand.cards]
        match_state['bot_attack_hand'] = [card.__dict__ for card in bot.attack_hand.cards]
        match_state['bot_defense_hand'] = [card.__dict__ for card in bot.defense_hand.cards]
        
        # Játék vége ellenőrzése
        game_over = False
        winner = None
        if match_state['player_injuries'] >= 2 or match_state['rounds_played'] >= 6:
            game_over = True
            winner = 'Bot' if match_state['player_injuries'] >= 2 else 'Játékos'
        elif match_state['bot_injuries'] >= 2:
            game_over = True
            winner = 'Játékos'
        
        session['match_state'] = match_state
        
        return jsonify({
            'player_card': str(selected_card) if match_state['attacker'] == 'Játékos' else str(player_defense_card),
            'bot_card': str(bot_card),
            'damage': damage,
            'injury': injury,
            'special_rule': special,
            'player_attack_hand': [str(card) for card in player.attack_hand.cards],
            'player_defense_hand': [str(card) for card in player.defense_hand.cards],
            'player_damage': match_state['player_damage'],
            'bot_damage': match_state['bot_damage'],
            'player_injuries': match_state['player_injuries'],
            'bot_injuries': match_state['bot_injuries'],
            'round': match_state['rounds_played'],
            'game_over': game_over,
            'winner': winner
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_outcome(is_player_attacker, attacker_card, defender_card):
    # Egyszerűsített eredmény számítás
    attacker_value = attacker_card.get_score_value()
    defender_value = defender_card.get_score_value()
    
    # Speciális szabályok
    if is_figure_or_ace(attacker_card) and defender_card.value in [2, 3]:
        return 0, True, "Attacker suffers serious injury"
    
    if is_figure_or_ace(defender_card):
        if attacker_card.value == 2:
            return 6, False, "Attacker 2 vs Defender figure/ace (+6 damage)"
        elif attacker_card.value == 3:
            return 0, False, "Attacker 3 vs Defender figure/ace (no damage)"
    
    if attacker_card.value == 4 and (attacker_value - defender_value) < 0:
        return 0, False, "4 card neutralizes defender's advantage"
    
    # Normál sebzés számítás
    damage = attacker_value - defender_value
    if damage > 0:
        return damage, False, None
    elif damage < 0:
        return 0, True, None
    else:
        return 0, False, None

@app.route('/get_defender_card', methods=['POST'])
def get_defender_card():
    """Visszaadja a védő által kijátszott lapot"""
    match_state = session.get('match_state')
    if not match_state:
        return jsonify({'error': 'Nincs aktív játék'}), 400
    
    try:
        # Játékállapot betöltése
        bot = BotPlayer("Bot", GreedyHighestValueStrategy())
        bot.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['bot_defense_hand']]
        
        defender_card = None
        
        if match_state['attacker'] == 'Játékos':
            # Játékos támad, Bot védekezik - Bot teszi le először a lapját
            if not match_state.get('bot_defense_order') or len(match_state['bot_defense_order']) == 0:
                return jsonify({'error': 'Bot defense order is empty'}), 500
            
            bot_card_dict = match_state['bot_defense_order'][0]  # Még ne távolítsuk el, csak nézzük meg
            defender_card = f"{Card.SUIT_EMOJIS.get(bot_card_dict['suit'], '')}{bot_card_dict['value']}"
        else:
            # Bot támad, Játékos védekezik - Játékos teszi le először a lapját
            # Itt a játékosnak kellene választania, de mivel nincs AI, random választunk
            player = BotPlayer("Játékos", RandomStrategy())
            player.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['player_defense_hand']]
            
            if len(player.defense_hand.cards) == 0:
                return jsonify({'error': 'Player has no defense cards left'}), 500
            
            defender_card_obj = player.defense_hand.cards[0]  # Első lapot vesszük
            defender_card = str(defender_card_obj)
        
        return jsonify({
            'defender_card': defender_card,
            'is_player_attacker': match_state['attacker'] == 'Játékos'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/respond_to_defender', methods=['POST'])
def respond_to_defender():
    """A támadó válaszol a védő lapjára"""
    match_state = session.get('match_state')
    if not match_state:
        return jsonify({'error': 'Nincs aktív játék'}), 400
    
    try:
        card_index = request.json.get('card_index')
        
        # Játékállapot betöltése
        player = BotPlayer("Játékos", RandomStrategy())
        bot = BotPlayer("Bot", GreedyHighestValueStrategy())
        
        # Kártyák visszaállítása
        player.attack_hand.cards = [Card(card['value'], card['suit']) for card in match_state['player_attack_hand']]
        player.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['player_defense_hand']]
        bot.attack_hand.cards = [Card(card['value'], card['suit']) for card in match_state['bot_attack_hand']]
        bot.defense_hand.cards = [Card(card['value'], card['suit']) for card in match_state['bot_defense_hand']]
        
        # Támadó kártya történet visszaállítása
        attacker_card_history = [Card(card['value'], card['suit']) for card in match_state.get('attacker_card_history', [])]
        
        # Védő és támadó lapjának meghatározása
        if match_state['attacker'] == 'Játékos':
            # Játékos támad, Bot védekezik
            bot_card_dict = match_state['bot_defense_order'].pop(0)
            bot_card = next(
                (card for card in bot.defense_hand.cards if card.value == bot_card_dict['value'] and card.suit == bot_card_dict['suit']),
                None
            )
            if bot_card:
                bot.defense_hand.remove_card(bot_card)
            else:
                return jsonify({'error': 'Bot defense card not found in hand'}), 500
            
            selected_card = player.attack_hand.cards[card_index]
            player.attack_hand.remove_card(selected_card)
            
            defender_card = bot_card
            attacker_card = selected_card
            
        else:
            # Bot támad, Játékos védekezik
            player_defense_card = player.defense_hand.cards[0]
            player.defense_hand.remove_card(player_defense_card)
            
            bot_attack_card = bot.attack_hand.cards[0]
            bot.attack_hand.remove_card(bot_attack_card)
            
            defender_card = player_defense_card
            attacker_card = bot_attack_card
        
        # Támadó kártya hozzáadása a történethez
        attacker_card_history.append(attacker_card)
        
        # Eredmény számítás bónuszokkal
        damage, injury, special_text, damage_breakdown = calculate_outcome_with_bonuses(
            match_state['attacker'] == 'Játékos',
            attacker_card,
            defender_card,
            attacker_card_history
        )
        
        # Játékállapot frissítése
        if match_state['attacker'] == 'Játékos':
            if injury:
                match_state['player_injuries'] += 1
            if damage > 0:
                match_state['bot_damage'] += damage
        else:
            if injury:
                match_state['bot_injuries'] += 1
            if damage > 0:
                match_state['player_damage'] += damage
        
        match_state['rounds_played'] += 1
        match_state['player_attack_hand'] = [{'value': card.value, 'suit': card.suit} for card in player.attack_hand.cards]
        match_state['player_defense_hand'] = [{'value': card.value, 'suit': card.suit} for card in player.defense_hand.cards]
        match_state['bot_attack_hand'] = [{'value': card.value, 'suit': card.suit} for card in bot.attack_hand.cards]
        match_state['bot_defense_hand'] = [{'value': card.value, 'suit': card.suit} for card in bot.defense_hand.cards]
        match_state['attacker_card_history'] = [{'value': card.value, 'suit': card.suit} for card in attacker_card_history]
        
        # Szakasz vége ellenőrzése
        phase_over = False
        phase_winner = None
        if match_state['player_injuries'] >= 3 or match_state['rounds_played'] >= 6:
            phase_over = True
            if match_state['player_injuries'] >= 3:
                phase_winner = 'Bot'
            elif match_state['bot_injuries'] >= 3:
                phase_winner = 'Játékos'
            else:
                # 6 kör után a kevesebb sebzést kapott nyer
                phase_winner = 'Játékos' if match_state['player_damage'] < match_state['bot_damage'] else 'Bot'
        elif match_state['bot_injuries'] >= 3:
            phase_over = True
            phase_winner = 'Játékos'
        
        # Ha a szakasz véget ért, frissítsük a mérkőzés történetet
        if phase_over:
            match_history = session.get('match_history', {})
            match_history['player_total_damage'] += match_state['player_damage']
            match_history['bot_total_damage'] += match_state['bot_damage']
            match_history['player_total_injuries'] += match_state['player_injuries']
            match_history['bot_total_injuries'] += match_state['bot_injuries']
            match_history['current_phase'] += 1
            match_history['phase_results'].append({
                'phase': match_history['current_phase'] - 1,
                'winner': phase_winner,
                'player_damage': match_state['player_damage'],
                'bot_damage': match_state['bot_damage'],
                'player_injuries': match_state['player_injuries'],
                'bot_injuries': match_state['bot_injuries']
            })
            session['match_history'] = match_history
        
        session['match_state'] = match_state
        
        return jsonify({
            'defender_card': str(defender_card),
            'attacker_card': str(attacker_card),
            'damage': damage,
            'injury': injury,
            'special_rule': special_text,
            'damage_breakdown': damage_breakdown,
            'player_attack_hand': [str(card) for card in player.attack_hand.cards],
            'player_defense_hand': [str(card) for card in player.defense_hand.cards],
            'player_damage': match_state['player_damage'],
            'bot_damage': match_state['bot_damage'],
            'player_injuries': match_state['player_injuries'],
            'bot_injuries': match_state['bot_injuries'],
            'round': match_state['rounds_played'],
            'phase_over': phase_over,
            'phase_winner': phase_winner,
            'match_history': session.get('match_history', {}) if phase_over else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)