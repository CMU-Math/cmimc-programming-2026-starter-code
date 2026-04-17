import click
import config
from engine import MazeEngine, MazeSimulator
import numpy as np
from visualizer import run_visualizer


@click.group()
def cli():
    pass

@cli.command()
def run():
    engine = MazeEngine()
    result = engine.grade(config.bot, config.ghost, config.graph_style, config.slots_style, config.seed)
    result.print_result()

@cli.command()
def compare():
    if config.seed == -1:
        config.seed = np.random.randint(1, 1000000)
    engine = MazeEngine()
    for (name, bot, ghost) in config.players:
        result = engine.grade(bot, ghost, config.graph_style, config.slots_style, config.seed)
        print(name)
        result.print_result()

@cli.command()
def full_run():
    engine = MazeEngine()
    total = 0
    fails = 0
    seeds = np.random.randint(1, 100000000, size=20)
    for seed in seeds:
        for graph_style in range(4):
            try:
                total += engine.grade(config.bot, config.ghost, graph_style, config.slots_style, seed).coins
            except:
                fails += 1
    print(f"Average across 20 seeds and 4 styles: {total / 80}")
    print(f"Fails across 20 seeds and 4 styles: {fails}")

@cli.command()
def full_compare():
    seeds = np.random.randint(1, 100000000, size=20)
    engine = MazeEngine()
    totals = {}
    fails = {}
    for (name, _, _) in config.players:
        totals[name] = 0
        fails[name] = 0
    engine = MazeEngine()
    for seed in seeds:
        for graph_style in range(4):
                for (name, bot, ghost) in config.players:
                    try:
                        result = engine.grade(bot, ghost, graph_style, config.slots_style, seed)
                        totals[name] += result.coins
                    except:
                        fails[name] += 1
    for (name, _, _) in config.players:
        print(f"{name}: {totals[name]} coins, {fails[name]} fails")

@cli.command()
def visualize():
    run_visualizer(config.bot, config.ghost, config.graph_style, config.slots_style, config.seed)

if __name__ == "__main__":
    cli()
