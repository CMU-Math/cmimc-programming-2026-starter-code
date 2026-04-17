from typing import List, Tuple, Any
import numpy as np

# Simple bot that stays at the first slot it finds
def BasicBot(step: int, total_steps: int, pos: int, last_pos: int, neighbors: List[int], has_slot: bool, slot_coins: int, data: Any) -> (int, Any):
    if has_slot:
        return (-1, None)
    return (neighbors[np.random.randint(0, len(neighbors))], 0)

# Simple ghost that stays at the first slot it finds
def BasicGhost(step: int, total_steps: int, pos: int, last_pos: int, neighbors: List[int], has_slot: bool, slot_coins: int, data: Any) -> (int, Any):
    if has_slot:
        return (-1, None)
    return (neighbors[np.random.randint(0, len(neighbors))], 0)
