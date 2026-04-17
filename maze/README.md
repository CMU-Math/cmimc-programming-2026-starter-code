# Maze

A competitive coin-collection game where a **Bot** and a **Ghost** traverse a graph, spinning slot machines to accumulate coins. The Bot has a strict 128-byte memory limit; the Ghost has unlimited memory.

---

## Installation

Python 3.13+ is required.

**With uv (recommended):**
```bash
uv sync
```

**With pip:**
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Project structure

| File / folder | Purpose |
|---|---|
| `engine.py` | `MazeSimulator`, `MazeEngine`, `Graph`, `Slot` — do not modify |
| `submission.py` | Your `SubmissionBot` and `SubmissionGhost` implementations |
| `config.py` | Simulation parameters (bot, ghost, graph style, seed) |
| `bots/bot.py` | Function signatures for Bot and Ghost |
| `bots/basic.py` | Simple reference implementations |
| `cli.py` | Command-line interface |
| `visualizer.py` | Interactive pygame visualizer |

---

## Configuration

Edit `config.py` before running:

```python
from submission import SubmissionBot, SubmissionGhost

bot         = SubmissionBot
ghost       = SubmissionGhost
seed        = -1      # -1 = random; set a fixed int for reproducibility
graph_style = 3       # 0 = very sparse, 1 = sparse, 2 = clustered, 3 = Halin
slots_style = 1       # 1 = distance-based slots
```

**Graph styles:**

| Value | Description |
|---|---|
| `0` | Very sparse random maze |
| `1` | Sparse random maze |
| `2` | 5 dense clusters with sparse inter-cluster edges |
| `3` | Halin graph (plane tree + leaf cycle) |

**Slot styles:**

| Value | Description |
|---|---|
| `1` | Distance-based: higher-value slots farther from the root |

---

## Running the simulation

All commands read their parameters from `config.py`.

```bash
# Run one simulation and print the coin total
python cli.py run

# Run the same seed against every bot/ghost pair listed in config.players
python cli.py compare

# Average coins across 20 random seeds × 4 graph styles
python cli.py full-run

# Same, for all players in config.players
python cli.py full-compare

# Open the interactive visualizer
python cli.py visualize
```

---

## Interactive visualizer

`python cli.py visualize` opens a 1280×800 pygame window.

**What you see:**

- **Slate-blue circles** — plain graph nodes
- **Gold circles** — slot nodes (machines you can spin)
- **Yellow circles** with a number — coins stored at a node
- **Blue circle** — Bot
- **Red circle** — Ghost
- Node labels are shown when `size ≤ 40`; hidden at the default size of 100

**Controls:**

| Key / action | Effect |
|---|---|
| `Space` | Play / Pause |
| `→` (right arrow) | Advance one step (while paused) |
| `R` | Reset — re-runs `initialize()` with the same parameters |
| `Esc` | Quit |
| Speed slider | Drag to set simulation speed (0.5 – 120 steps/sec, log scale) |
| Pause / Resume button | Same as `Space` |
| Step button | Same as `→` |
| Reset button | Same as `R` |

Movement is smoothly animated between nodes. Slot pulls trigger a brief yellow-white flash on the node.

You can also call the visualizer directly from Python:

```python
from visualizer import run_visualizer
from submission import SubmissionBot, SubmissionGhost

run_visualizer(SubmissionBot, SubmissionGhost, graph_style=3, slots_style=1, seed=42)
```

---

## Writing a bot

A Bot (and Ghost) is a plain function with this signature:

```python
def Bot(step, total_steps, pos, last_pos, neighbors, has_slot, slot_coins, data):
    ...
    return (target, new_data)
```

| Parameter | Type | Description |
|---|---|---|
| `step` | `int` | Current step number (1-indexed) |
| `total_steps` | `int` | Total steps in the simulation |
| `pos` | `int` | Current node index |
| `last_pos` | `int` | Node index before the last move |
| `neighbors` | `list[int]` | Adjacent node indices |
| `has_slot` | `bool` | Whether the current node has a slot machine |
| `slot_coins` | `int` | Coins currently stored at this node |
| `data` | `Any` | Persistent state from the previous step |

**Return value:** `(target, new_data)`

- `target = -1` — spin the slot machine at the current node (stay put)
- `target = <neighbor index>` — move to that neighbor
- `new_data` — any Python object to pass to the next step (**128-byte limit** for the Bot; unlimited for the Ghost)

See `bots/basic.py` for a minimal working example and `submission.py` for a full implementation.
