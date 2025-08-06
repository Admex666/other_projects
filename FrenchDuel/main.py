from player import BotPlayer
from match import Match
from strategy import RandomStrategy, GreedyHighestValueStrategy
from simulation import Simulation
from analysis import Analyzer # Import Analyzer for direct use in main

def run_single_duel_phase():
    """
    Runs a single duel phase between two bot players and prints the results.
    """
    print("--- Running Single Duel Phase ---")
    player1 = BotPlayer("Knight Arthur", strategy=RandomStrategy())
    player2 = BotPlayer("Knight Lancelot", strategy=GreedyHighestValueStrategy())
    duel_match = Match(player1, player2)
    phase_results = duel_match.play_duel_phase(player1.name)

    print("\n=====================================")
    print("       FRENCHDUEL PHASE SUMMARY      ")
    print("=====================================")
    print(f"Attacker for this phase: {phase_results['attacker_name']}")
    print(f"Defender for this phase: {phase_results['defender_name']}")
    print(f"Attacker's final serious injuries: {phase_results['attacker_final_injuries']}")
    print(f"Defender's total damage taken: {phase_results['defender_final_damage']}")
    print(f"Phase Winner: {phase_results['phase_winner']}")
    print("=====================================")

def run_large_simulation_and_analyze():
    """
    Runs a large number of matches between two different strategies,
    saves the log, and then performs analysis.
    """
    print("--- Running Large-Scale Simulation ---")
    num_matches_to_run = 1000
    log_filename = "simulation_log.json"

    # Define the two strategies to compare
    strategy_a = RandomStrategy()
    strategy_b = GreedyHighestValueStrategy()

    # Create and run the simulation
    simulation = Simulation(strategy_a, strategy_b)
    simulation.run_simulation(num_matches_to_run)
    
    # Save the detailed log after simulation
    simulation.save_log_to_file(log_filename)

    # Perform analysis
    print("\n--- Running Analysis ---")
    analyzer = Analyzer(log_file=log_filename)
    analyzer.analyze_win_rates()
    analyzer.analyze_damage_and_injuries()
    analyzer.analyze_damage_per_rank()
    analyzer.analyze_injury_rate_per_rank()
    analyzer.analyze_damage_source_breakdown()
    analyzer.analyze_win_rate_by_drafted_cards()
    analyzer.analyze_draft_rate_vs_win_rate()
    analyzer.analyze_bot_performance_stability()


if __name__ == "__main__":
    # You can choose which mode to run by commenting/uncommenting the lines below
    # run_single_duel_phase()
    run_large_simulation_and_analyze()
