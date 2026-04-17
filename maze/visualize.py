import networkx as nx
import matplotlib.pyplot as plt


def visualize_graph(n: int, adj: list[list[int]], title: str = "Graph"):
    """
    Visualize an undirected graph given its number of vertices and adjacency list.

    Args:
        n:     Number of vertices (labeled 0..n-1)
        adj:   Adjacency list — adj[i] is the list of neighbors of vertex i
        title: Title shown on the plot
    """
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u, neighbors in enumerate(adj):
        for v in neighbors:
            G.add_edge(u, v)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(title, fontsize=14, fontweight='bold', pad=14)
    ax.axis('off')

    # Kamada-Kawai minimizes a spring energy that explicitly penalises long
    # edges, so connected nodes end up close together. Fall back gracefully
    # for disconnected graphs (KK requires a connected graph).
    if nx.is_connected(G):
        pos = nx.kamada_kawai_layout(G)
    else:
        # Layout each component with KK, then tile components on a grid
        pos = {}
        components = list(nx.connected_components(G))
        cols = max(1, int(len(components) ** 0.5))
        for idx, comp in enumerate(components):
            sub = G.subgraph(comp)
            if len(comp) == 1:
                sub_pos = {list(comp)[0]: (0.0, 0.0)}
            else:
                sub_pos = nx.kamada_kawai_layout(sub)
            row, col = divmod(idx, cols)
            for node, (x, y) in sub_pos.items():
                pos[node] = (x + col * 2.5, y - row * 2.5)

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color='#378ADD',
                           node_size=600,
                           edgecolors='#185FA5',
                           linewidths=1.5)

    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_color='white',
                            font_size=11,
                            font_weight='bold')

    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color='#888780',
                           width=1.5)

    stats = (f"vertices: {n}   "
             f"edges: {G.number_of_edges()}   "
             f"components: {nx.number_connected_components(G)}")
    ax.text(0.01, 0.01, stats, transform=ax.transAxes,
            fontsize=9, color='#888780', va='bottom')

    plt.tight_layout()
    plt.show()


# ── example usage ────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Cactus graph (9 vertices)
    # Cycle 0-1-2-0, path 0-3, cycle 3-4-5-3, path 3-6, cycle 6-7-8-6
    n_cactus = 9
    adj_cactus = [
        [1, 2],        # 0
        [0, 2],        # 1
        [1, 0, 3],     # 2
        [2, 4, 5, 6],  # 3
        [3, 5],        # 4
        [4, 3],        # 5
        [3, 7, 8],     # 6
        [6, 8],        # 7
        [7, 6],        # 8
    ]
    visualize_graph(n_cactus, adj_cactus, title="Cactus Graph")

    # Petersen graph
    n_petersen = 10
    adj_petersen = [
        [1, 4, 5],   # 0
        [0, 2, 6],   # 1
        [1, 3, 7],   # 2
        [2, 4, 8],   # 3
        [3, 0, 9],   # 4
        [0, 7, 8],   # 5
        [1, 8, 9],   # 6
        [2, 9, 5],   # 7
        [3, 5, 6],   # 8
        [4, 6, 7],   # 9
    ]
    visualize_graph(n_petersen, adj_petersen, title="Petersen Graph")