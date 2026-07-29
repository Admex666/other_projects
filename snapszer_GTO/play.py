"""
Interactive Schnapsen Terminal CLI Game - Play against GTOExploitBot!
Rich Terminal UI with ASCII/Unicode card graphics and full rule support.
"""

import os
import random
import sys
from typing import Optional, List
from schnapsen.game import (
    Bot,
    Card,
    GamePhase,
    Move,
    PlayerPerspective,
    Rank,
    Suit,
    SchnapsenGamePlayEngine,
)
from src.bot import GTOExploitBot

# Unicode Symbols & Color formatting
SUIT_SYMBOLS = {
    Suit.HEARTS: "♥",
    Suit.DIAMONDS: "♦",
    Suit.CLUBS: "♣",
    Suit.SPADES: "♠",
}

SUIT_NAMES = {
    Suit.HEARTS: "Hearts",
    Suit.DIAMONDS: "Diamonds",
    Suit.CLUBS: "Clubs",
    Suit.SPADES: "Spades",
}

RANK_DISPLAY = {
    Rank.ACE: ("A", 11),
    Rank.TEN: ("10", 10),
    Rank.KING: ("K", 4),
    Rank.QUEEN: ("Q", 3),
    Rank.JACK: ("J", 2),
}


def card_str(card: Card) -> str:
    symbol, pts = RANK_DISPLAY[card.rank]
    suit_icon = SUIT_SYMBOLS[card.suit]
    return f"[{symbol}{suit_icon} ({pts}p)]"


def move_str(move: Move) -> str:
    if move.is_marriage():
        suit_name = SUIT_NAMES[move.queen_card.suit]
        icon = SUIT_SYMBOLS[move.queen_card.suit]
        return f"👑 MARRIAGE 20/40 in {icon} {suit_name} (Queen {card_str(move.queen_card)} & King {card_str(move.king_card)})"
    if move.is_trump_exchange():
        return f"🔄 TRUMP EXCHANGE: Swap Jack for face-up Trump card"
    return f"🃏 Play Card {card_str(move.card)}"


class HumanCLIPlayer(Bot):
    """
    Rich Terminal Interactive Player.
    """

    def __init__(self, name: str = "Human") -> None:
        super().__init__(name)

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        print("\n" + "=" * 65)
        print(f"                SCHNAPSEN MATCH - YOUR TURN ({self})")
        print("=" * 65)

        phase_number = 2 if perspective.get_phase() == GamePhase.TWO else 1
        phase_desc = (
            "⚠️ PHASE 2: Talon is empty/closed! MUST FOLLOW SUIT & TRUMP!"
            if phase_number == 2
            else "🟢 PHASE 1: Talon is open (Cards drawn after each trick)."
        )
        print(f"Status: {phase_desc}")

        trump_card = perspective.get_trump_card()
        if trump_card:
            print(f"Trump Card on Talon: {card_str(trump_card)} ({SUIT_NAMES[trump_card.suit]})")

        talon_count = perspective.get_talon_size()
        print(f"Talon Cards Remaining: {talon_count}")

        won_cards = perspective.get_won_cards()
        own_pts = sum(RANK_DISPLAY[c.rank][1] for c in won_cards)
        opp_won = perspective.get_opponent_won_cards()
        opp_pts = sum(RANK_DISPLAY[c.rank][1] for c in opp_won)

        print(f"\nSCORE BOARD:")
        print(f"  ➜ YOU ({self}):            {own_pts} / 66 points ({len(won_cards)} cards won)")
        print(f"  ➜ OPPONENT (GTOExploitBot): ~{opp_pts} / 66 points ({len(opp_won)} cards won)")

        if leader_move:
            print(f"\n➡️ OPPONENT LED FOR THIS TRICK: {move_str(leader_move)}")
            print("   (You are FOLLOWER - pick your response card below)")
        else:
            print("\n👑 YOU ARE LEADER FOR THIS TRICK - Pick a card to lead:")

        print("\nYOUR HAND CARDS:")
        for idx, card in enumerate(perspective.get_hand(), 1):
            print(f"  {idx}. {card_str(card)} {SUIT_NAMES[card.suit]}")

        valid_moves: List[Move] = perspective.valid_moves()
        print("\nLEGAL MOVES:")
        for idx, move in enumerate(valid_moves, 1):
            print(f"  [{idx}] {move_str(move)}")

        while True:
            try:
                raw = input(f"\n👉 Enter choice number [1-{len(valid_moves)}]: ").strip()
                if not raw:
                    continue
                choice_idx = int(raw) - 1
                if 0 <= choice_idx < len(valid_moves):
                    chosen_move = valid_moves[choice_idx]
                    print(f"\n✔ YOU SELECTED: {move_str(chosen_move)}")
                    print("-" * 65)
                    return chosen_move
                print(f"❌ Invalid selection. Please enter a number between 1 and {len(valid_moves)}.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except (KeyboardInterrupt, EOFError):
                print("\n\nGame exited by user.")
                sys.exit(0)


def main():
    print("\n" + "♠♥♦♣" * 16)
    print("        WELCOME TO SCHNAPSEN GTO AI TERMINAL ARENA        ")
    print("♠♥♦♣" * 16)

    try:
        user_name = input("\nEnter your name [Player]: ").strip() or "Player"
    except (KeyboardInterrupt, EOFError):
        user_name = "Player"

    human = HumanCLIPlayer(user_name)

    seed = random.randint(1000, 99999)
    gto_bot = GTOExploitBot(name="GTOExploitBot", num_samples=16, depth=4, rand=random.Random(seed))

    engine = SchnapsenGamePlayEngine()
    game_rng = random.Random()

    print(f"\nGame initialized! You are playing against {gto_bot}.\n")

    winner, game_points, score = engine.play_game(human, gto_bot, game_rng)

    print("\n" + "=" * 65)
    print("                     GAME FINAL RESULT                     ")
    print("=" * 65)
    if winner is human:
        print(f"🎉 CONGRATULATIONS {user_name.upper()}! YOU DEFEATED GTOExploitBot!")
        print(f"   Game Points Earned: {game_points} GP")
    else:
        print(f"🤖 GTOExploitBot WON THE MATCH for {game_points} Game Points.")
        print(f"   Better luck next time!")

    print(f"   Winner Trick Score: {score.direct_points} direct points")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
