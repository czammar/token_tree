"""Script to construct and visualize hierarchical token graphs using NetworkX and Matplotlib."""

import argparse
import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable


class NetworkXVisualizer:
    """Builds and renders custom hierarchical NetworkX directed graphs from JSON datasets."""

    @staticmethod
    def render(
        nodes_file: str,
        edges_file: str,
        figure_width: int,
        figure_height: int,
    ) -> None:
        """
        Loads graph data, computes hierarchical layout, maps edge weights to
        width/color, and renders via Matplotlib.

        :param nodes_file: Path to source JSON file containing nodes.
        :param edges_file: Path to source JSON file containing edges.
        :param figure_width: Width dimension of output figure.
        :param figure_height: Height dimension of output figure.
        """
        with open(nodes_file, "r", encoding="utf-8") as f:
            nodes_data: List[Dict[str, Any]] = json.load(f)
        with open(edges_file, "r", encoding="utf-8") as f:
            edges_data: List[Dict[str, Any]] = json.load(f)

        graph = nx.DiGraph()

        # 1. Add Nodes
        for n in nodes_data:
            graph.add_node(
                n["id_contexto"],
                label=repr(n["name"]),
                is_root=n.get("is_root", False),
                num_visits=n["num_visits"],
            )

        # 2. Add Edges with Weights
        for a in edges_data:
            graph.add_edge(a["origin"], a["destination"], weight=a["weight"])

        # 3. Calculate Hierarchical Layout (Tree layout by level)
        pos: Dict[str, Tuple[float, float]] = {}
        root_id: str = [n for n, d in graph.in_degree() if d == 0][0]

        levels: Dict[str, int] = {}
        for node in graph.nodes():
            path_length = len(nx.shortest_path(
                graph,
                source=root_id,
                target=node)) - 1
            levels[node] = path_length

        nodes_by_level: Dict[int, List[str]] = {}
        for node, lvl in levels.items():
            nodes_by_level.setdefault(lvl, []).append(node)

        max_lvl: int = max(nodes_by_level.keys()) if nodes_by_level else 1
        for lvl, nodes_in_lvl in nodes_by_level.items():
            total_nodes: int = len(nodes_in_lvl)
            for idx, node in enumerate(nodes_in_lvl):
                x: float = lvl / max_lvl
                y: float = (idx + 1) / (total_nodes + 1)
                pos[node] = (x, y)

        # 4. Map Edge Weights (Sampling frequency) to Width and
        # Color Intensities
        edge_weights: List[int] = [
            graph[u][v]["weight"] for u, v in graph.edges()
            ]
        min_w, max_w = min(edge_weights), max(edge_weights)

        if max_w > min_w:
            edge_widths: List[float] = [
                1.0 + 4.0 * ((w - min_w) / (max_w - min_w))
                for w in edge_weights
            ]
        else:
            edge_widths = [1.5 for _ in edge_weights]

        cmap = plt.cm.Blues
        norm = Normalize(vmin=min_w - 0.5, vmax=max_w)
        edge_colors = [cmap(norm(w)) for w in edge_weights]

        # 5. Render Figure
        plt.figure(figsize=(figure_width, figure_height))
        plt.title(
            "Token Tree (Edge Width and Intensity = Sampling Frequency)",
            fontsize=13,
            fontweight="bold",
        )

        nx.draw_networkx_edges(
            graph,
            pos,
            width=edge_widths,
            edge_color=edge_colors,
            arrows=True,
            arrowsize=12,
            connectionstyle="arc3,rad=0.05",
        )

        node_colors: List[str] = [
            "#FF6B6B" if graph.nodes[n].get("is_root") else "#4A90E2"
            for n in graph.nodes()
        ]
        nx.draw_networkx_nodes(
            graph, pos, node_size=1800, node_color=node_colors, alpha=0.9
        )

        labels: Dict[str, str] = nx.get_node_attributes(graph, "label")
        nx.draw_networkx_labels(
            graph,
            pos,
            labels=labels,
            font_size=8,
            font_color="black",
            font_weight="bold",
        )

        # Colorbar configuration
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(
            sm, ax=plt.gca(), orientation="horizontal", pad=0.03, shrink=0.6
        )
        cbar.set_label("Sampling Frequency (Edge Traversal Visits)")

        plt.axis("off")
        plt.tight_layout()
        plt.show()


def main() -> None:
    """Parses arguments and executes NetworkX graph rendering."""
    parser = argparse.ArgumentParser(
        description="Render hierarchical NetworkX graph from JSON files."
    )
    parser.add_argument(
        "--nodes-file",
        type=str,
        default="nodes.json",
        help="Input nodes JSON file path",
    )
    parser.add_argument(
        "--edges-file",
        type=str,
        default="edges.json",
        help="Input edges JSON file path",
    )
    parser.add_argument(
        "--width", type=int, default=16, help="Matplotlib plot figure width"
    )
    parser.add_argument(
        "--height", type=int, default=10, help="Matplotlib plot figure height"
    )

    args = parser.parse_args()

    NetworkXVisualizer.render(
        nodes_file=args.nodes_file,
        edges_file=args.edges_file,
        figure_width=args.width,
        figure_height=args.height,
    )


if __name__ == "__main__":
    main()
