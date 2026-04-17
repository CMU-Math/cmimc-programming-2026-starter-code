from typing import List, Tuple, Type
from bots.bot import Bot, Ghost
import numpy as np
# import math
# from visualize import visualize_graph
import networkx as nx
import sys

PRIMITIVES = {int, float, str, bool, bytes, type(None)}
CONTAINERS = {list, tuple, set, frozenset}

class DataSizeError(Exception):
    def __init__(self, data, size):
        super().__init__(f"Your data object takes {size} bytes and is: {data}")

def sizeof_validator(obj, _getsizeof=sys.getsizeof):
    """
    Validates that obj contains only primitives and dicts/lists/tuples/sets,
    and returns the total deep size in bytes.
    Raises TypeError with the offending path if an invalid type is found.
    """
    size = _getsizeof(obj)
    t = type(obj)

    if t in PRIMITIVES:
        pass  # valid leaf, size already counted

    elif t is dict:
        _sizeof = sizeof_validator
        for k, v in obj.items():
            size += _sizeof(k)
            size += _sizeof(v)

    elif t in CONTAINERS:
        _sizeof = sizeof_validator
        for i, item in enumerate(obj):
            size += _sizeof(item)

    else:
        raise TypeError(f"In your data, value {obj} has unsupported type: {type(obj).__name__}")

    return size


class Slot:
    def __init__(self, alpha, rng):
        self.rng = np.random.default_rng(rng.integers(0, 2**63))
        self.alpha = alpha

    def get(self):
        x = self.rng.random() or 1e-300
        y = min(self.alpha * 10, self.alpha // x)
        return int(y)


class Node:
    def __init__(self, slot=None):
        self.neighbors = []
        self.slot = slot

    def add_edge(self, other):
        self.neighbors.append(other)

    def set_slot(self, slot):
        self.slot = slot


class Graph:
    def __init__(self, size):
        self.nodes = [Node() for i in range(size)]
        self.n = size
    
    # Note: At some point the labels need to be mapped randomly to avoid using the numbers to determine structure
    def generate_clustered(self, n_clusters: int, intra_density: float, inter_density: float, rng):
        """
        Partition vertices into n_clusters clusters. Within each cluster,
        include each edge with probability intra_density. Between clusters,
        include each edge with probability inter_density. A spanning tree
        across clusters guarantees connectivity.

        Typical values: intra_density=0.7, inter_density=0.05
        """
        # Partition vertices into clusters as evenly as possible
        indices = list(range(self.n))
        rng.shuffle(indices)
        clusters = [[] for _ in range(n_clusters)]
        for i, v in enumerate(indices):
            clusters[i % n_clusters].append(v)

        def guarantee_connected(cluster):
            """Wilson's algorithm restricted to the given cluster."""
            if len(cluster) <= 1:
                return
            in_tree = {cluster[0]}
            for start in cluster[1:]:
                if start in in_tree:
                    continue
                path = [start]
                visited = {start}
                while path[-1] not in in_tree:
                    v = int(rng.choice(cluster))
                    if v in visited:
                        idx = path.index(v)
                        for node in path[idx + 1:]:
                            visited.discard(node)
                        path = path[:idx + 1]
                    else:
                        path.append(v)
                        visited.add(v)
                for i in range(len(path) - 1):
                    self.connect(path[i], path[i + 1])
                in_tree.update(path)

        # Dense intra-cluster edges
        for cluster in clusters:
            for i in range(len(cluster)):
                for j in range(i + 1, len(cluster)):
                    if rng.random() < intra_density:
                        self.connect(cluster[i], cluster[j])
            # Guarantee the cluster is connected regardless of Bernoulli luck
            guarantee_connected(cluster)

        # Guarantee inter-cluster connectivity with a spanning tree over clusters
        # Shuffle cluster order and chain them: 0-1, 1-2, ..., (k-2)-(k-1)
        cluster_order = list(range(n_clusters))
        rng.shuffle(cluster_order)
        for i in range(len(cluster_order) - 1):
            a = int(rng.choice(clusters[cluster_order[i]]))
            b = int(rng.choice(clusters[cluster_order[i + 1]]))
            self.connect(a, b)

        # Sparse additional inter-cluster edges
        for ci in range(n_clusters):
            for cj in range(ci + 1, n_clusters):
                for a in clusters[ci]:
                    for b in clusters[cj]:
                        if b not in self.nodes[a].neighbors and rng.random() < inter_density:
                            self.connect(a, b)

    def generate_maze_cactus(self):
        pass

    def generate_maze_random_sparsity(self, sparsity: float, rng):
        in_tree = [False] * self.n
        in_tree[0] = True
        in_tree_count = 1
        while in_tree_count < self.n:
            u = int(rng.choice([i for i in range(self.n) if not in_tree[i]]))
            path = [u]
            visited = {u}

            while not in_tree[path[-1]]:
                v = rng.integers(0, self.n)
                if v in visited:
                    idx = path.index(v)
                    for node in path[idx + 1:]:
                        visited.discard(node)
                    path = path[:idx + 1]
                else:
                    path.append(v)
                    visited.add(v)
            for i in range(len(path) - 1):
                self.connect(path[i], path[i + 1])
                in_tree[path[i]] = True
            in_tree_count = sum(in_tree)

        max_edges = self.n * (self.n - 1) // 2
        tree_edges = self.n - 1
        remaining_slots = max_edges - tree_edges
        target_edges = int(sparsity * max_edges)
        extra_needed = max(0, target_edges - tree_edges)
        p_extra = extra_needed / remaining_slots if remaining_slots > 0 else 0
        
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if j not in self.nodes[i].neighbors and rng.random() < p_extra:
                    self.connect(i, j)


    def generate_halin(self, rng):
        """
        Generate a Halin graph: a plane tree plus a cycle through all leaves
        in DFS planar order. Every internal node has tree-degree >= 3.
        Requires n >= 4.
        """
        if self.n < 4:
            raise ValueError("Halin graphs require n >= 4")

        # I internals, n-I leaves. Need n - I >= I + 2, so I <= (n-2)//2.
        max_internals = (self.n - 2) // 2
        num_internals = int(rng.integers(1, max_internals + 1))

        verts = list(range(self.n))
        rng.shuffle(verts)
        internals = verts[:num_internals]
        leaves = verts[num_internals:]

        children = [[] for _ in range(self.n)]
        tree_degree = [0] * self.n  # final degree in the tree

        # Step 1: random spanning tree on the internals, rooted at internals[0].
        # Cap tree_degree at 3 so step 2's leaf demand is exactly I + 2 ≤ n - I.
        root = internals[0]
        in_tree = [root]
        for v in internals[1:]:
            available = [p for p in in_tree if tree_degree[p] < 3]
            p = int(rng.choice(available))
            children[p].append(v)
            tree_degree[p] += 1
            tree_degree[v] += 1  # parent edge
            in_tree.append(v)

        # Step 2: give every internal enough leaf-children to reach degree 3
        leaf_iter = iter(leaves)
        for v in internals:
            while tree_degree[v] < 3:
                c = next(leaf_iter)
                children[v].append(c)
                tree_degree[v] += 1
                tree_degree[c] = 1

        # Step 3: distribute remaining leaves to random internals
        for c in leaf_iter:
            p = int(rng.choice(internals))
            children[p].append(c)
            tree_degree[p] += 1
            tree_degree[c] = 1

        # Randomize planar embedding
        for v in internals:
            rng.shuffle(children[v])

        # Step 4: DFS to collect leaves in planar order
        leaves_in_order = []
        stack = [root]
        while stack:
            node = stack.pop()
            if not children[node]:
                leaves_in_order.append(node)
            else:
                for c in reversed(children[node]):
                    stack.append(c)

        # Step 5: emit tree edges + leaf cycle
        for p in range(self.n):
            for c in children[p]:
                self.connect(p, c)

        for i in range(len(leaves_in_order)):
            a = leaves_in_order[i]
            b = leaves_in_order[(i + 1) % len(leaves_in_order)]
            self.connect(a, b)

    def slots_random(self, slot_sparsity: float, min_alpha: int, max_alpha: int, rng):
        alpha_list = []
        freq = (max_alpha - min_alpha + 1) * 10 + 1
        for a in range(min_alpha, max_alpha + 1):
            for _ in range(freq):
                alpha_list.append(a)
            freq -= 10

        for i in range(self.n):
            if rng.random() < slot_sparsity:
                self.set_slot(i, Slot(int(rng.choice(alpha_list)), rng))

    def slots_distance(self, start: int, distance_base: float, distance_scaling: float, alpha_scaling: int, rng):
        G = nx.Graph()
        for u, node in enumerate(self.nodes):
            for v in node.neighbors:
                G.add_edge(u, v)
        
        distances = nx.single_source_shortest_path_length(G, source=start)

        best_slot = 0
        for i in range(self.n):
            if distances[i] == 0:
                continue
            if rng.random() < (distance_base + distance_scaling * distances[i]):
                next_slot = int(rng.random() * (alpha_scaling * distances[i]))
                self.set_slot(i, Slot(next_slot, rng))
                best_slot = max(best_slot, next_slot)
        return best_slot

    def connect(self, one, two):
        one, two = int(one), int(two)
        if two in self.nodes[one].neighbors or one == two:
            return
        self.nodes[one].add_edge(two)
        self.nodes[two].add_edge(one)

    def set_slot(self, node, slot):
        self.nodes[node].set_slot(slot)


class MazeResult:
    def __init__(self, coins: float, seed: int):
        self.coins = coins
        self.seed = seed

    def print_result(self) -> None:
        print(f"Coins: {self.coins}")


class MazeSimulator:
    def initialize(self, bot: Type[Bot], ghost: Type[Ghost], graph_style: int, slots_style: int, seed: int, size: int, steps: int) -> None:
        self.rng = np.random.default_rng(seed if seed != -1 else None)
        self.graph = Graph(size)
        if graph_style == 0:
            self.graph.generate_maze_random_sparsity(0.02, self.rng)
        elif graph_style == 1:
            self.graph.generate_maze_random_sparsity(0.1, self.rng)
        elif graph_style == 2:
            self.graph.generate_clustered(5, .2, 0.002, self.rng)
        elif graph_style == 3:
            self.graph.generate_halin(self.rng)

        if slots_style == 1:
            best_slot = self.graph.slots_distance(0, .03, .03, 3, self.rng)
            
            # The following code provides a very loose upper bound on the maximum number of coins

            # slot = Slot(best_slot)
            # total = 0
            # for _ in range(steps):
            #     total += slot.get()
            # print(f"Theoretical best: {total}")
        elif slots_style == 2:
            self.graph.slots_random(0.2, 2, 10, self.rng)
        else:
            pass

        # Uncomment the below two lines if you want to see the generated graph
        # adj_list = [self.graph.nodes[i].neighbors for i in range(size)]
        # visualize_graph(size, adj_list)

        # Random vertex permutation to hide internal labels from bot/ghost.
        # Vertex 0 stays fixed (it's the documented start); others are shuffled.
        externals = list(range(1, size))
        self.rng.shuffle(externals)
        self.perm = [0] + externals          # perm[internal] = external
        self.inv_perm = [0] * size
        for i, e in enumerate(self.perm):
            self.inv_perm[e] = i

        self.most_data = 0
        self.size = size
        self.bot = bot
        self.ghost = ghost
        self.coins = 0
        self.bot_info = {"pos": 0, "last_pos": -1, "data": None}
        self.ghost_info = {"pos": 0, "last_pos": -1, "data": None}
        self.total_steps = steps
        self.current_step = 0
        self.coins_stored = {}

    def step(self) -> bool:
        if self.current_step >= self.total_steps:
            return True
        self.current_step += 1
        # First simulate the bot and get its step
        bot_pos = self.bot_info["pos"]
        bot_ext_neighbors = [self.perm[n] for n in self.graph.nodes[bot_pos].neighbors]
        try:
            ret = self.bot(self.current_step, self.total_steps, self.perm[bot_pos], 
                        self.perm[self.bot_info["last_pos"]], bot_ext_neighbors, 
                        self.graph.nodes[bot_pos].slot is not None, self.coins_stored.get(bot_pos, 0), self.bot_info["data"])
        except Exception as e:
            raise Exception(f"Your SubmissionBot function raised an exception: {str(e)}")
        try:
            (bot_target, self.bot_info["data"]) = ret
        except:
            raise TypeError(f"Your SubmissionBot returned {ret}, which is not a tuple.")
        self.bot_info["last_pos"] = bot_pos
        data_size = sizeof_validator(self.bot_info["data"])
        if data_size > 128:
            raise DataSizeError(self.bot_info["data"], data_size)
        self.most_data = max(self.most_data, data_size)

        # Now simulate the ghost and get its step
        ghost_pos = self.ghost_info["pos"]
        ghost_ext_neighbors = [self.perm[n] for n in self.graph.nodes[ghost_pos].neighbors]
        try:
            ret = self.ghost(self.current_step, self.total_steps, self.perm[ghost_pos], 
                        self.perm[self.ghost_info["last_pos"]], ghost_ext_neighbors, 
                        self.graph.nodes[ghost_pos].slot is not None, self.coins_stored.get(ghost_pos, 0), self.ghost_info["data"])
        except Exception as e:
            raise Exception(f"Your SubmissionGhost function raised an exception: {str(e)}")
        try:
            (ghost_target, self.ghost_info["data"]) = ret
        except:
            raise TypeError(f"Your SubmissionGhost returned {ret}, which is not a tuple.")
        self.ghost_info["last_pos"] = ghost_pos

        # Could limit ghost data to some very large value just for memory but I think a global memory limit for the run is fine
        # Also this is kinda slow

        # data_size = sizeof_validator(self.ghost_info["data"])
        # if data_size > 1048576:
        #     raise Exception(str(f"Bot data too large with {data_size} bytes"))

        if type(bot_target) is not int:
            raise Exception(f"Your bot returned a non-int action: {bot_target!r}")
        if type(ghost_target) is not int:
            raise Exception(f"Your ghost returned a non-int action: {ghost_target!r}")

        if bot_target != -1:
            if bot_target not in bot_ext_neighbors:
                raise Exception(f"Your bot returned an invalid action: {bot_target}")
            bot_target = self.inv_perm[bot_target]

        if ghost_target != -1:
            if ghost_target not in ghost_ext_neighbors:
                raise Exception(f"Your ghost returned an invalid action: {ghost_target}")
            ghost_target = self.inv_perm[ghost_target]

        if self.coins_stored.get(bot_pos, 0) > 0:
            self.coins += self.coins_stored[bot_pos]
            self.coins_stored[bot_pos] = 0
        # Now update for slot pulls and positions
        if bot_target == -1 and self.graph.nodes[bot_pos].slot is not None:
            spin = self.graph.nodes[bot_pos].slot.get()
            self.coins_stored[bot_pos] = self.coins_stored.get(bot_pos, 0) + spin
        elif bot_target in self.graph.nodes[bot_pos].neighbors:
            self.bot_info["pos"] = bot_target
        
        if ghost_target == -1 and (bot_target != -1 or bot_pos != ghost_pos) and self.graph.nodes[ghost_pos].slot is not None:
            spin = self.graph.nodes[ghost_pos].slot.get()
            self.coins_stored[ghost_pos] = min(50, self.coins_stored.get(ghost_pos, 0) + spin)
        elif ghost_target in self.graph.nodes[ghost_pos].neighbors:
            self.ghost_info["pos"] = ghost_target
        return self.current_step == self.total_steps


class MazeEngine:
    def grade(self, bot: Type[Bot], ghost: Type[Ghost], graph_style: int, slots_style: int, seed: int) -> MazeResult:
        simulator = MazeSimulator()
        simulator.initialize(bot, ghost, graph_style, slots_style, seed, 100, 2000)
        stop = False
        while not stop:
            stop = simulator.step()
        coins = simulator.coins
        # print(simulator.most_data)
        return MazeResult(coins, seed)
