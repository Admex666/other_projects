from flask import Flask, render_template, jsonify, request, session
from player import BotPlayer
from match import Match
from strategy import RandomStrategy, GreedyHighestValueStrategy
from cards import Card, is_figure_or_ace
import json

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
        
        # Játékos és bot létrehozása
        player = BotPlayer("Játékos", RandomStrategy())
        bot = BotPlayer("Bot", GreedyHighestValueStrategy())
    
        # Új mérkőzés
        current_match = Match(player, bot)
        
        # Kezdő támadó beállítása
        starting_attacker = player.name if request.json.get('start_as_attacker') else bot.name
        current_match._assign_roles(starting_attacker)
        
        # Kártyák osztása
        current_match._draft_attack_cards()
        current_match._draft_defense_cards()
        
        # Védőkártyák sorrendjének meghatározása
        if not player.is_attacker:
            bot_defense_order = bot.choose_defense_order() if not player.is_attacker else []
        
        # Játékállapot mentése session-be
        session['match_state'] = {
            'player_attack_hand': [{'value': card.value, 'suit': card.suit} for card in player.attack_hand.cards],
            'player_defense_hand': [{'value': card.value, 'suit': card.suit} for card in player.defense_hand.cards],
            'bot_attack_hand': [{'value': card.value, 'suit': card.suit} for card in bot.attack_hand.cards],
            'bot_defense_hand': [{'value': card.value, 'suit': card.suit} for card in bot.defense_hand.cards],
            'player_damage': player.damage,
            'bot_damage': bot.damage,
            'player_injuries': player.serious_injuries,
            'bot_injuries': bot.serious_injuries,
            'attacker': current_match.attacker.name,
            'defender': current_match.defender.name,
            'rounds_played': 0,
            'bot_defense_order': [card.__dict__ for card in bot_defense_order] if not player.is_attacker else []
        }
        
        return jsonify({
            'status': 'ready',
            'player_attack_hand': [str(card) for card in player.attack_hand.cards],
            'player_defense_hand': [str(card) for card in player.defense_hand.cards],
            'is_attacker': player.is_attacker,
            'bot_defense_order': [str(card) for card in bot_defense_order] if not player.is_attacker else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
        
        # Bot lépése
        if match_state['attacker'] == 'Játékos':
            # Játékos támad, bot védekezik
            if not match_state.get('bot_defense_order'):  # Ha üres a defense order
                bot_defense_order = bot.choose_defense_order(bot.defense_hand.cards)
                match_state['bot_defense_order'] = [{'value': card.value, 'suit': card.suit} for card in bot_defense_order]
            
            # Itt már biztosan van elem a listában
            bot_card_dict = match_state['bot_defense_order'].pop(0)
            # Find the card object in the bot's hand that matches the one to be played
            bot_card = next(
                (card for card in bot.defense_hand.cards if card.value == bot_card_dict['value'] and card.suit == bot_card_dict['suit']),
                None
            )
            if bot_card:
                bot.defense_hand.remove_card(bot_card)
            else:
                # Handle error if the card isn't found
                return jsonify({'error': 'Bot defense card not found in hand'}), 500
            player_defense_card = None
        else:
            # Bot támad, játékos védekezik
            bot_card = bot.attack_hand.cards[0]
            bot.attack_hand.remove_card(bot_card)
            player_defense_card = player.defense_hand.cards[0]
            player.defense_hand.remove_card(player_defense_card)
        
        # Eredmény számítás
        damage, injury, special = calculate_outcome(
            match_state['attacker'] == 'Játékos',
            selected_card if match_state['attacker'] == 'Játékos' else bot_card,
            bot_card if match_state['attacker'] == 'Játékos' else player_defense_card
        )
        
        # Játékállapot frissítése
        if match_state['attacker'] == 'Játékos':
            if damage > 0:
                match_state['bot_damage'] += damage
            if injury:
                match_state['player_injuries'] += 1
        else:
            if damage > 0:
                match_state['player_damage'] += damage
            if injury:
                match_state['bot_injuries'] += 1
        
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

if __name__ == '__main__':
    app.run(debug=True)