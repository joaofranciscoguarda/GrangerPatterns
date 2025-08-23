import matplotlib.pyplot as plt
import networkx as nx


def plot_network_graph(G, title, output_path, vmin=None, vmax=None):
    """Plot a network graph of Granger Causality in a standardized circular layout"""
    plt.figure(figsize=(14, 10))

    # Standardized node order for all figures
    standard_nodelist = ["F3", "F4", "C3", "C4", "P3", "P4"]
    # Compute positions for all possible nodes
    pos = nx.circular_layout(standard_nodelist)

    # Swap F3 -> C3, C3 -> C4, C4 -> F3
    if all(node in pos for node in ["F3", "C3", "C4"]):
        temp = pos["F3"].copy()
        pos["F3"] = pos["C3"]
        pos["C3"] = pos["C4"]
        pos["C4"] = temp
    # Filter positions to only those present in G
    pos = {node: pos[node] for node in G.nodes() if node in pos}

    # Electrode colors (fallback to gray if not specified)
    electrode_colors = {
        "F3": "#ff7f0e",
        "F4": "#1f77b4",
        "C3": "#2ca02c",
        "C4": "#d62728",
        "P3": "#9467bd",
        "P4": "#8c564b",
    }

    # Get edge weights and apply consistent scaling if provided
    if G.edges():
        edge_weights = [G[u][v]["weight"] for u, v in G.edges()]

        if vmin is not None and vmax is not None and vmax > vmin:
            # Normalize edge weights to consistent scale (0-1 range)
            normalized_weights = []
            for weight in edge_weights:
                # Normalize weight to 0-1 range based on global min/max
                normalized = (weight - vmin) / (vmax - vmin)
                # Scale for visualization (multiply by scaling factor) - increased minimum thickness
                normalized_weights.append(
                    max(normalized * 16, 1)
                )  # Minimum width of 1.5 (increased from 0.6), max of 16
            edge_widths = normalized_weights
            scale_info = (
                f"Edge thickness scaled by global range: {vmin:.6f} - {vmax:.6f}"
            )
        else:
            # Use original scaling if no vmin/vmax provided - increased minimum thickness
            edge_widths = [max(weight * 8000, 1) for weight in edge_weights]
            if edge_weights:
                scale_info = f"Edge thickness scaled by local range: {min(edge_weights):.6f} - {max(edge_weights):.6f}"
            else:
                scale_info = "No edges to display"
    else:
        edge_widths = []
        edge_weights = []
        scale_info = "No edges above threshold"

    # Draw nodes with custom colors
    nodelist = list(G.nodes())
    node_colors = [electrode_colors.get(node, "#333333") for node in nodelist]
    nx.draw_networkx_nodes(
        G, pos, nodelist=nodelist, node_size=1500, node_color=node_colors, alpha=0.8
    )

    # Draw edges with varying width based on weight
    if G.edges() and edge_widths:
        edgelist = list(G.edges())
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=edgelist,
            width=edge_widths,
            alpha=0.6,
            arrowsize=20,
            arrowstyle="->",
        )

    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight="bold")

    # Add title and scale information
    plt.title(title, fontsize=16, pad=20)

    # Add scale information as subtitle
    plt.figtext(0.5, 0.02, scale_info, ha="center", fontsize=10, style="italic")

    # Create a legend for edge thickness if there are edges
    if edge_weights:
        # Create legend showing edge thickness scale
        legend_elements = []
        if vmin is not None and vmax is not None:
            # Show normalized scale
            legend_weights = [vmin, (vmin + vmax) / 2, vmax]
            legend_labels = [
                f"Min: {vmin:.6f}",
                f"Mid: {(vmin + vmax) / 2:.6f}",
                f"Max: {vmax:.6f}",
            ]
        else:
            # Show local scale
            min_weight = min(edge_weights)
            max_weight = max(edge_weights)
            mid_weight = (min_weight + max_weight) / 2
            legend_weights = [min_weight, mid_weight, max_weight]
            legend_labels = [
                f"Min: {min_weight:.6f}",
                f"Mid: {mid_weight:.6f}",
                f"Max: {max_weight:.6f}",
            ]

        # Create sample lines for legend
        from matplotlib.lines import Line2D

        legend_elements = []
        for i, (weight, label) in enumerate(zip(legend_weights, legend_labels)):
            if vmin is not None and vmax is not None and vmax > vmin:
                normalized = (weight - vmin) / (vmax - vmin)
                line_width = (
                    max(normalized * 16, 1) / 2
                )  # Scale down for legend, increased minimum
            else:
                line_width = (
                    max(weight * 8000, 1) / 2
                )  # Scale down for legend, increased minimum

            legend_elements.append(
                Line2D(
                    [0], [0], color="gray", linewidth=line_width, alpha=0.6, label=label
                )
            )

        # Add legend
        plt.legend(
            handles=legend_elements,
            loc="upper left",
            bbox_to_anchor=(0.02, 0.98),
            title="Edge Weight Scale",
            title_fontsize=10,
            fontsize=9,
        )

    plt.axis("off")
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
