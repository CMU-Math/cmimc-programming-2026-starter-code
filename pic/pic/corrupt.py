import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CorruptConfig(ABC):
    pass

class Corrupt(ABC):
    @abstractmethod
    def corrupt(self, config: CorruptConfig, pic: list[list[float]]) -> list[list[float | None]]:
        pass


@dataclass
class BlockMaskNoiseConfig(CorruptConfig):
    block_size: int = 5
    p_shared: float = 0.2
    noise_std_lo: float = 0.05
    noise_std_hi: float = 0.25
    blur_sigma_lo: float = 0.5
    blur_sigma_hi: float = 1.0


def _gaussian_blur(grid: list[list[float]], m: int, n: int, sigma: float) -> list[list[float]]:
    radius = max(1, int(3 * sigma))
    kernel = [math.exp(-0.5 * (x / sigma) ** 2) for x in range(-radius, radius + 1)]
    ksum = sum(kernel)
    kernel = [k / ksum for k in kernel]

    # horizontal pass
    temp = [[0.0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            val = 0.0
            for i, k in enumerate(kernel):
                cc = max(0, min(n - 1, c + i - radius))
                val += k * grid[r][cc]
            temp[r][c] = val

    # vertical pass
    out = [[0.0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            val = 0.0
            for i, k in enumerate(kernel):
                rr = max(0, min(m - 1, r + i - radius))
                val += k * temp[rr][c]
            out[r][c] = val

    return out


def _add_noise(grid: list[list[float]], m: int, n: int, noise_std: float) -> list[list[float]]:
    return [
        [max(0.0, min(1.0, grid[r][c] + random.gauss(0, noise_std))) for c in range(n)]
        for r in range(m)
    ]


class BlockMaskNoise:
    def corrupt_pair(
        self, config: BlockMaskNoiseConfig, pic: list[list[float]]
    ) -> tuple[list[list[float | None]], list[list[float | None]]]:
        h = len(pic)
        w = len(pic[0])
        bs = config.block_size

        # Independent blur + noise for each player
        blur_sigma_1 = random.uniform(config.blur_sigma_lo, config.blur_sigma_hi)
        blur_sigma_2 = random.uniform(config.blur_sigma_lo, config.blur_sigma_hi)
        noise_std_1 = random.uniform(config.noise_std_lo, config.noise_std_hi)
        noise_std_2 = random.uniform(config.noise_std_lo, config.noise_std_hi)

        blurred_1 = _add_noise(_gaussian_blur(pic, h, w, blur_sigma_1), h, w, noise_std_1)
        blurred_2 = _add_noise(_gaussian_blur(pic, h, w, blur_sigma_2), h, w, noise_std_2)

        # Determine block grid dimensions
        blocks_r = (h + bs - 1) // bs
        blocks_c = (w + bs - 1) // bs

        # Assign each block: 0 = P1 only, 1 = P2 only, 2 = shared
        # Guarantee both players have ~equal number of blocked-out blocks
        total_blocks = blocks_r * blocks_c
        num_shared = round(total_blocks * config.p_shared)
        num_exclusive = total_blocks - num_shared
        num_p1 = num_exclusive // 2
        num_p2 = num_exclusive - num_p1
        assignments = [0] * num_p1 + [1] * num_p2 + [2] * num_shared
        random.shuffle(assignments)

        out1: list[list[float | None]] = [[None] * w for _ in range(h)]
        out2: list[list[float | None]] = [[None] * w for _ in range(h)]

        for i in range(h):
            for j in range(w):
                br = i // bs
                bc = j // bs
                assignment = assignments[br * blocks_c + bc]

                if assignment == 0 or assignment == 2:
                    out1[i][j] = blurred_1[i][j]
                if assignment == 1 or assignment == 2:
                    out2[i][j] = blurred_2[i][j]

        return out1, out2
