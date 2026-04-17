#!/usr/bin/env python3
"""Visualize PIC games: original, corrupted, and recovered images side by side."""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from pic.engine import Engine
from pic.generate import (
    GenerateRandomCircles, GenerateRandomCirclesConfig,
    GenerateBlobs, GenerateBlobsConfig,
    GenerateVoronoi, GenerateVoronoiConfig,
    GeneratePiecewiseConstant, GeneratePiecewiseConstantConfig,
)
from pic.corrupt import BlockMaskNoise

# ──────────────────────────────────────────────
# MODIFY THESE: import your own strategy classes
# ──────────────────────────────────────────────
from submission import SubmissionStrategy
from pic.strategy.catalog.baseline import Baseline

PLAYER_ONE = SubmissionStrategy
PLAYER_TWO = Baseline
# ──────────────────────────────────────────────

N = 50

GENERATORS = [
    ("Random Circles",      GenerateRandomCircles(),     GenerateRandomCirclesConfig(m=N, n=N, num_circles=10, min_radius=3.0, max_radius=15.0)),
    ("Blobs (Binary)",      GenerateBlobs(),             GenerateBlobsConfig(m=N, n=N, sigma=3.0)),
    ("Voronoi",             GenerateVoronoi(),           GenerateVoronoiConfig(m=N, n=N)),
    ("Piecewise Constant",  GeneratePiecewiseConstant(), GeneratePiecewiseConstantConfig(m=N, n=N, num_splits=20)),
]

corrupt = BlockMaskNoise()

# Colormap: grayscale but with purple for missing pixels
PURPLE = np.array([0.5, 0.0, 0.5])  # RGB purple


def corrupted_to_rgba(corrupted):
    """Convert an image (with None for missing/unknown pixels) to an RGBA array.
    Missing pixels are shown in purple, known pixels in grayscale."""
    rows = len(corrupted)
    cols = len(corrupted[0])
    rgba = np.zeros((rows, cols, 3))
    for r in range(rows):
        for c in range(cols):
            v = corrupted[r][c]
            if v is None:
                rgba[r, c] = PURPLE
            else:
                rgba[r, c] = [v, v, v]
    return rgba


fig, axes = plt.subplots(len(GENERATORS), 5, figsize=(14, 3 * len(GENERATORS)))

col_titles = ["Original", "P1 Corrupted", "P1 Recovered", "P2 Corrupted", "P2 Recovered"]

for col_idx, title in enumerate(col_titles):
    axes[0, col_idx].set_title(title, fontsize=11, fontweight="bold")

for row_idx, (name, gen, gen_config) in enumerate(GENERATORS):
    engine = Engine(gen, gen_config, corrupt, gen.corrupt_config)
    (s1, s2), (original, corrupt_one, corrupt_two, recovered_one, recovered_two) = \
        engine.play(PLAYER_ONE, PLAYER_TWO, return_images=True)

    axes[row_idx, 0].imshow(np.array(original), cmap="gray", vmin=0, vmax=1)
    axes[row_idx, 1].imshow(corrupted_to_rgba(corrupt_one))
    axes[row_idx, 2].imshow(corrupted_to_rgba(recovered_one))
    axes[row_idx, 3].imshow(corrupted_to_rgba(corrupt_two))
    axes[row_idx, 4].imshow(corrupted_to_rgba(recovered_two))

    axes[row_idx, 0].set_ylabel(f"{name}\nP1={s1:.3f} P2={s2:.3f}", fontsize=9)

    for col_idx in range(5):
        axes[row_idx, col_idx].set_xticks([])
        axes[row_idx, col_idx].set_yticks([])

plt.tight_layout()
plt.savefig("visualize.png", dpi=150)
plt.show()
