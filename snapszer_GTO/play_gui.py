"""
Interactive Web GUI Schnapsen Game - Play against GTOExploitBot in your Browser!
Uses SchnapsenServer built-in web engine.
"""

import random
import webbrowser
import time
from schnapsen.game import SchnapsenGamePlayEngine
from schnapsen.bots.gui.guibot import SchnapsenServer
from src.bot import GTOExploitBot


def main():
    print("=" * 65)
    print("       STARTING SCHNAPSEN GTO AI WEB SERVER & BROWSER GUI      ")
    print("=" * 65)

    host = "127.0.0.1"
    port = 8080
    url = f"http://{host}:{port}"

    print(f"\n[1/2] Launching Schnapsen Web Server on {url}...")

    with SchnapsenServer(host_name=host, port=port) as server:
        gui_player = server.make_gui_bot("Player")

        seed = random.randint(1, 99999)
        gto_bot = GTOExploitBot(name="GTOExploitBot", num_samples=16, depth=4, rand=random.Random(seed))

        engine = SchnapsenGamePlayEngine()
        game_rng = random.Random()

        print(f"[2/2] Opening browser interface at {url}...")
        time.sleep(1)
        webbrowser.open(url)

        print("\n>>> Game is active! Play in your browser window. <<<")
        print("Press Ctrl+C in terminal to stop server.\n")

        try:
            winner, points, score = engine.play_game(gui_player, gto_bot, game_rng)
            print("\n" + "=" * 65)
            print(f"GAME ENDED! Winner: {winner} | Game Points: {points}")
            print("=" * 65)
        except KeyboardInterrupt:
            print("\nServer stopped by user.")


if __name__ == "__main__":
    main()
