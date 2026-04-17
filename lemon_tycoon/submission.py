from players.player import Player
from typing import Dict, List, Tuple
import math
import random
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)


# Don't change the name of this class when you submit!
class SubmissionPlayer(Player):
    def __init__(self, player_id, num_players, factory_bit_width, sell_price,
                 buy_price, sabotage_cost, initial_lemons, goal_lemons, max_rounds):
        self.player_id = player_id
        self.buy_price = buy_price
        self.max_factory_id = 2 ** factory_bit_width

    def play(self, round_number, your_lemons, your_factories, all_lemons,
             destroyed_factory_counts, sabotages_by_player
             ) -> Tuple[List[int], List[int], List[int]]:
        # Buy random factories with whatever lemons we have
        num_to_buy = math.floor(your_lemons // self.buy_price)
        buy = [random.randint(1, self.max_factory_id) for _ in range(num_to_buy)]
        return buy, [], []
