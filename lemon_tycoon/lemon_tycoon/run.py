#!/usr/bin/env python3
"""Run a local Lemon Tycoon game."""

from engine import GameEngine
from submission import SubmissionPlayer

GAME_PARAMS = {
    "num_players": 4,
    "factory_bit_width": 4,
    "sell_price": 5.0,
    "buy_price": 15.0,
    "sabotage_cost": 15.0,
    "initial_lemons": 30.0,
    "goal_lemons": 2000.0,
    "max_rounds": 200,
}

PLAYER_CTORS = [SubmissionPlayer] * 4


def run_game():
    engine = GameEngine(PLAYER_CTORS, GAME_PARAMS)

    while not engine.is_game_over():
        engine.step()
        state = engine.get_state()
        if state["round"] % 10 == 0 or state["game_over"]:
            print(f"\nRound {state['round']}:")
            for pid in range(GAME_PARAMS["num_players"]):
                print(f"  Player {pid}: {state['lemons'][pid]:.2f} lemons")

    state = engine.get_state()
    rankings = engine.get_rankings()

    print("\n" + "=" * 40)
    print("GAME OVER!")

    if state["winner"]:
        winner_id = state["winner"][0]
        print(f"Winner: Player {winner_id} with {state['lemons'][winner_id]:.2f} lemons!")

    print("\nFinal Rankings:")
    for rank, pid in enumerate(rankings):
        print(f"  {rank + 1}. Player {pid}: {state['lemons'][pid]:.2f} lemons")


if __name__ == "__main__":
    run_game()
