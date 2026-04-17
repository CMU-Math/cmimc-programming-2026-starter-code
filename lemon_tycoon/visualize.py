#!/usr/bin/env python3
"""Animated visualizer for Lemon Tycoon games.

Runs a full game, records per-round state, then plays it back as an
animation showing lemon counts over time and each player's factory
inventory. Red vertical bands mark rounds in which sabotage occurred.
"""

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from engine import GameEngine
from submission import SubmissionPlayer

# ──────────────────────────────────────────────
# MODIFY THESE: import your own player classes
# ──────────────────────────────────────────────
PLAYER_CTORS = [SubmissionPlayer] * 4
# ──────────────────────────────────────────────

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

PLAYER_COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
FRAME_INTERVAL_MS = 80


def simulate(player_ctors, game_params):
    engine = GameEngine(player_ctors, game_params)
    num_players = game_params["num_players"]

    state = engine.get_state()
    history = {
        "lemons": [state["lemons"].copy()],
        "factories": [state["factories"].copy()],
        "sabotages": [{}],
        "sabotages_by_player": [[[] for _ in range(num_players)]],
    }

    while not engine.is_game_over():
        engine.step()
        state = engine.get_state()
        history["lemons"].append(state["lemons"].copy())
        history["factories"].append(state["factories"].copy())
        # _prev_sabotages / _prev_sabotages_by_player are refreshed each step.
        history["sabotages"].append(dict(engine._prev_sabotages))
        history["sabotages_by_player"].append(
            [s.copy() for s in engine._prev_sabotages_by_player]
        )

    history["winner"] = engine._winner
    history["num_frames"] = len(history["lemons"])
    return history


def animate(history, game_params):
    num_players = game_params["num_players"]
    num_ids = 2 ** game_params["factory_bit_width"]
    goal = game_params["goal_lemons"]
    num_frames = history["num_frames"]

    lemon_history = np.stack(history["lemons"])
    factory_history = np.stack(history["factories"])

    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, num_players, height_ratios=[2, 1])

    ax_lemons = fig.add_subplot(gs[0, :])
    ax_factories = [fig.add_subplot(gs[1, p]) for p in range(num_players)]

    lemon_lines = []
    for p in range(num_players):
        (line,) = ax_lemons.plot([], [], color=PLAYER_COLORS[p], label=f"Player {p}", linewidth=2)
        lemon_lines.append(line)

    ax_lemons.axhline(goal, color="gray", linestyle="--", linewidth=1, label=f"Goal ({goal:.0f})")
    ax_lemons.set_xlim(0, max(num_frames - 1, 1))
    ax_lemons.set_ylim(0, max(lemon_history.max() * 1.1, goal * 1.1))
    ax_lemons.set_xlabel("Round")
    ax_lemons.set_ylabel("Lemons")
    ax_lemons.legend(loc="upper left")
    ax_lemons.grid(True, alpha=0.3)

    id_labels = np.arange(1, num_ids + 1)
    factory_bars = []
    max_factory_count = max(int(factory_history.max()), 1)
    for p in range(num_players):
        bars = ax_factories[p].bar(id_labels, np.zeros(num_ids), color=PLAYER_COLORS[p])
        factory_bars.append(bars)
        ax_factories[p].set_title(f"Player {p}")
        ax_factories[p].set_xlabel("Factory ID")
        ax_factories[p].set_ylim(0, max_factory_count + 1)
        ax_factories[p].set_xticks(id_labels)
        ax_factories[p].tick_params(axis="x", labelsize=7)

    ax_factories[0].set_ylabel("Count")

    title = fig.suptitle("", fontsize=14)
    drawn_sabotage_frames = set()

    def update(frame):
        xs = np.arange(frame + 1)
        for p in range(num_players):
            lemon_lines[p].set_data(xs, lemon_history[: frame + 1, p])

        factories_now = factory_history[frame]
        for p in range(num_players):
            for i, bar in enumerate(factory_bars[p]):
                bar.set_height(factories_now[p, i])

        if history["sabotages"][frame] and frame not in drawn_sabotage_frames:
            ax_lemons.axvline(frame, color="red", alpha=0.25, linewidth=1.5, zorder=0)
            drawn_sabotage_frames.add(frame)

        winner_str = ""
        if frame == num_frames - 1:
            if history["winner"]:
                winner_str = f" — Winner: Player {history['winner'][0]}"
            else:
                rankings = np.argsort(-lemon_history[-1]).tolist()
                winner_str = f" — Time out. Leader: Player {rankings[0]}"
        title.set_text(f"Round {frame} / {num_frames - 1}{winner_str}")

        return []

    anim = animation.FuncAnimation(
        fig,
        update,
        frames=num_frames,
        interval=FRAME_INTERVAL_MS,
        blit=False,
        repeat=False,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
    return anim


if __name__ == "__main__":
    history = simulate(PLAYER_CTORS, GAME_PARAMS)
    animate(history, GAME_PARAMS)
