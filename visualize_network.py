import matplotlib.pyplot as plt
import networkx as nx
import os

def plot_network_graph(G, title, output_path):
    """Plot a network graph of Granger Causality in a standardized circular layout"""
    plt.figure(figsize=(12, 10))
    
    # Standardized node order for all figures
    standard_nodelist = ['F3', 'F4', 'C3', 'C4', 'P3', 'P4']
    # Compute positions for all possible nodes
    pos = nx.circular_layout(standard_nodelist)

    # Swap F3 -> C3, C3 -> C4, C4 -> F3
    if all(node in pos for node in ['F3', 'C3', 'C4']):
        temp = pos['F3'].copy()
        pos['F3'] = pos['C3']
        pos['C3'] = pos['C4']
        pos['C4'] = temp
    # Filter positions to only those present in G
    pos = {node: pos[node] for node in G.nodes() if node in pos}
    
    # Electrode colors (fallback to gray if not specified)
    electrode_colors = {
        'F3': '#ff7f0e', 'F4': '#1f77b4',
        'C3': '#2ca02c', 'C4': '#d62728',
        'P3': '#9467bd', 'P4': '#8c564b',
    }
    
    # Get edge weights for width scaling
    edge_weights = [G[u][v]['weight'] * 5000 for u, v in G.edges()]
    
    # Draw nodes with custom colors
    nodelist = list(G.nodes())
    node_colors = [electrode_colors.get(node, '#333333') for node in nodelist]
    nx.draw_networkx_nodes(G, pos, nodelist=nodelist, node_size=1500, node_color=node_colors, alpha=0.8)
    
    # Draw edges with varying width based on weight
    edgelist = list(G.edges())
    edge_widths = edge_weights if len(edge_weights) > 0 else [1.0 for _ in edgelist]
    nx.draw_networkx_edges(G, pos, edgelist=edgelist, width=edge_widths, alpha=0.6, 
                          arrowsize=20, arrowstyle='->')
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold')
    
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close() 