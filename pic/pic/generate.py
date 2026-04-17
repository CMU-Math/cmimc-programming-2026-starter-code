import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .corrupt import BlockMaskNoiseConfig


@dataclass
class GenerateConfig(ABC):
    pass

class Generate(ABC):
    corrupt_config: BlockMaskNoiseConfig = BlockMaskNoiseConfig()

    @abstractmethod
    def generate(self, config: GenerateConfig) -> list[list[float]]:
        pass


@dataclass
class GenerateRandomCirclesConfig(GenerateConfig):
    m: int
    n: int
    num_circles: int
    min_radius: float = 1.0
    max_radius: float = 10.0

class GenerateRandomCircles(Generate):
    corrupt_config = BlockMaskNoiseConfig(blur_sigma_lo=1.0, blur_sigma_hi=3.0)

    def generate(self, config: GenerateRandomCirclesConfig) -> list[list[float]]:
        pic = [[0.0 for _ in range(config.n)] for _ in range(config.m)]
        for _ in range(config.num_circles):
            cy = random.uniform(0, config.m)
            cx = random.uniform(0, config.n)
            r = random.uniform(config.min_radius, config.max_radius)
            r_sq = r * r
            for i in range(config.m):
                for j in range(config.n):
                    if (i - cy) ** 2 + (j - cx) ** 2 <= r_sq:
                        pic[i][j] = 1.0 - pic[i][j]
        return pic


@dataclass
class GenerateBlobsConfig(GenerateConfig):
    m: int
    n: int
    sigma: float = 2.0

class GenerateBlobs(Generate):
    corrupt_config = BlockMaskNoiseConfig(blur_sigma_lo=1.0, blur_sigma_hi=3.0)

    def generate(self, config: GenerateBlobsConfig) -> list[list[float]]:
        noise = [[random.gauss(0, 1) for _ in range(config.n)] for _ in range(config.m)]
        smooth = _gaussian_blur(noise, config.m, config.n, config.sigma)
        return [[1.0 if smooth[r][c] > 0 else 0.0 for c in range(config.n)] for r in range(config.m)]


@dataclass
class GenerateVoronoiConfig(GenerateConfig):
    m: int
    n: int
    num_seeds: int = 20

class GenerateVoronoi(Generate):
    corrupt_config = BlockMaskNoiseConfig(blur_sigma_lo=0.9, blur_sigma_hi=1.0)

    def generate(self, config: GenerateVoronoiConfig) -> list[list[float]]:
        seeds = [
            (random.uniform(0, config.m), random.uniform(0, config.n), random.random())
            for _ in range(config.num_seeds)
        ]

        img = [[0.0] * config.n for _ in range(config.m)]
        for i in range(config.m):
            for j in range(config.n):
                best_dist = float("inf")
                best_val = 0.0
                for sy, sx, val in seeds:
                    d = (i - sy) ** 2 + (j - sx) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_val = val
                img[i][j] = best_val

        return img


@dataclass
class GeneratePiecewiseConstantConfig(GenerateConfig):
    m: int
    n: int
    num_splits: int = 6

class GeneratePiecewiseConstant(Generate):
    corrupt_config = BlockMaskNoiseConfig(blur_sigma_lo=1.0, blur_sigma_hi=1.5)

    def generate(self, config: GeneratePiecewiseConstantConfig) -> list[list[float]]:
        img = [[0.0] * config.n for _ in range(config.m)]
        regions = [(0, 0, config.m, config.n)]

        for _ in range(config.num_splits):
            idx = random.randint(0, len(regions) - 1)
            r1, c1, r2, c2 = regions.pop(idx)

            h = r2 - r1
            w = c2 - c1

            if h < 4 and w < 4:
                regions.append((r1, c1, r2, c2))
                continue

            if h > w:
                split = random.randint(r1 + 2, r2 - 2)
                regions.append((r1, c1, split, c2))
                regions.append((split, c1, r2, c2))
            else:
                split = random.randint(c1 + 2, c2 - 2)
                regions.append((r1, c1, r2, split))
                regions.append((r1, split, r2, c2))

        for r1, c1, r2, c2 in regions:
            val = random.random()
            for r in range(r1, r2):
                for c in range(c1, c2):
                    img[r][c] = val

        return img


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
                cc = c + i - radius
                cc = max(0, min(n - 1, cc))
                val += k * grid[r][cc]
            temp[r][c] = val

    # vertical pass
    out = [[0.0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            val = 0.0
            for i, k in enumerate(kernel):
                rr = r + i - radius
                rr = max(0, min(m - 1, rr))
                val += k * temp[rr][c]
            out[r][c] = val

    return out
