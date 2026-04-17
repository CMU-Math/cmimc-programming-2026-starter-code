from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class Player(ABC):
    @abstractmethod
    def __init__(
        self,
        player_id: int,
        num_players: int,
        factory_bit_width: int,
        sell_price: float,
        buy_price: float,
        sabotage_cost: float,
        initial_lemons: float,
        goal_lemons: float,
        max_rounds: int,
    ):
        pass

    @abstractmethod
    def play(
        self,
        round_number: int,
        your_lemons: float,
        your_factories: List[int],
        all_lemons: List[float],
        destroyed_factory_counts: Dict[int, int],
        sabotages_by_player: List[List[int]],
    ) -> Tuple[List[int], List[int], List[int]]:
        pass
