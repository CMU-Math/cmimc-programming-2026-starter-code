#!/usr/bin/env python3
"""Run a local PIC game."""

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

print(f"{'Generator':<22} {'P1 Score':>10} {'P2 Score':>10} {'Winner':>10}")
print("-" * 56)

for name, gen, gen_config in GENERATORS:
    engine = Engine(gen, gen_config, corrupt, gen.corrupt_config)
    s1, s2 = engine.play(PLAYER_ONE, PLAYER_TWO)
    if s1 < s2:
        winner = "P1"
    elif s2 < s1:
        winner = "P2"
    else:
        winner = "Tie"
    print(f"{name:<22} {s1:>10.4f} {s2:>10.4f} {winner:>10}")
