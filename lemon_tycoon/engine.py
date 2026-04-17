"""Game engine for Lemon Tycoon. Use run.py to run."""

import numpy as np
from typing import Any, Dict, List, Mapping, Sequence, Type

from players.player import Player


class GameEngine:

    def __init__(
        self,
        player_ctors: Sequence[Type[Player]],
        game_params: Mapping[str, Any],
    ):
        assert len(player_ctors) == game_params["num_players"]

        self._players = [
            player_ctor(player_id=pid, **game_params)
            for pid, player_ctor in enumerate(player_ctors)
        ]
        self._game_params = game_params

        num_players = game_params["num_players"]
        num_ids = 2 ** game_params["factory_bit_width"]
        self._lemons = np.full(num_players, game_params["initial_lemons"], dtype=float)
        self._factories = np.zeros((num_players, num_ids), dtype=int)
        self._production_rates = 2 * np.log2(np.arange(1, num_ids + 1))

        self._round = 0
        self._winner = []
        self._prev_sabotages = {}
        self._prev_sabotages_by_player = [[] for _ in range(num_players)]
        self._game_over = False

    def step(self):
        """Simulate one round of the game."""
        if self._game_over:
            return

        game_params = self._game_params
        buy_price = game_params["buy_price"]
        sell_price = game_params["sell_price"]
        sabotage_cost = game_params["sabotage_cost"]
        num_players = game_params["num_players"]
        num_ids = 2 ** game_params["factory_bit_width"]

        buy_actions = np.zeros((num_players, num_ids), dtype=int)
        sell_actions = np.zeros((num_players, num_ids), dtype=int)
        sabotage_actions = [[] for _ in range(num_players)]

        for pid, player in enumerate(self._players):
            factories_to_buy, factories_to_sell, ids_to_sabotage = player.play(
                round_number=self._round,
                your_lemons=self._lemons[pid],
                your_factories=self._factories[pid].tolist(),
                all_lemons=self._lemons.tolist(),
                destroyed_factory_counts=self._prev_sabotages.copy(),
                sabotages_by_player=[s.copy() for s in self._prev_sabotages_by_player],
            )

            for id_val in factories_to_buy:
                if 1 <= id_val <= num_ids:
                    buy_actions[pid, id_val - 1] += 1

            for id_val in factories_to_sell:
                if 1 <= id_val <= num_ids:
                    sell_actions[pid, id_val - 1] += 1

            sabotage_actions[pid] = ids_to_sabotage if isinstance(ids_to_sabotage, list) else []

        # 1. Process sells on existing factories
        sell_actions = np.minimum(sell_actions, self._factories)
        self._factories -= sell_actions
        self._lemons += sell_actions.sum(axis=1) * sell_price

        # 2. Process buys into separate new_factories
        new_factories = np.zeros((num_players, num_ids), dtype=int)
        buy_costs = buy_actions.sum(axis=1) * buy_price
        valid_buys = buy_costs <= self._lemons
        for pid in range(num_players):
            if valid_buys[pid]:
                self._lemons[pid] -= buy_costs[pid]
                new_factories[pid] = buy_actions[pid]

        # 3. Process sabotages on existing factories only
        sabotaged_ids = set()
        self._prev_sabotages = {}
        self._prev_sabotages_by_player = [[] for _ in range(num_players)]

        for pid in range(num_players):
            for id_val in sabotage_actions[pid]:
                if 1 <= id_val <= num_ids:
                    if self._lemons[pid] >= sabotage_cost:
                        sabotaged_ids.add(id_val)
                        self._lemons[pid] -= sabotage_cost
                        self._prev_sabotages_by_player[pid].append(id_val)

        for id_val in sabotaged_ids:
            id_idx = id_val - 1
            self._prev_sabotages[id_val] = int(self._factories[:, id_idx].sum())
            self._factories[:, id_idx] = 0

        # 4. Production from pre-existing, non-sabotaged factories
        production = self._factories @ self._production_rates
        self._lemons += production

        # 5. Merge new factories
        self._factories += new_factories

        # Check win condition
        winners = np.where(self._lemons >= game_params["goal_lemons"])[0]
        if len(winners) > 0:
            max_lemons = self._lemons[winners].max()
            self._winner = winners[self._lemons[winners] == max_lemons].tolist()
            self._game_over = True
            for pid in range(num_players):
                if pid not in self._winner:
                    self._lemons[pid] += self._factories[pid].sum() * sell_price
                    self._factories[pid] = 0

        self._round += 1

        if self._round >= game_params["max_rounds"]:
            self._game_over = True
            self._lemons += self._factories.sum(axis=1) * sell_price
            self._factories[:] = 0

    def get_rankings(self) -> List[int]:
        """Return player IDs sorted by lemon count (descending)."""
        return np.argsort(-self._lemons).tolist()

    def get_state(self) -> Dict[str, Any]:
        """Return current game state."""
        return {
            "round": self._round,
            "lemons": self._lemons.copy(),
            "factories": self._factories.copy(),
            "winner": self._winner,
            "game_over": self._game_over,
        }

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self._game_over
