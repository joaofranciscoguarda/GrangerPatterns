import matplotlib.pyplot as plt
import networkx as nx
import os

def plot_network_graph(G, title, output_path):
    """Plot a network graph of Granger Causality"""
    plt.figure(figsize=(12, 10))
    
    # Default to fixed positions based on typical EEG montage
    pos = {
        'F3': (-1, 1), 'F4': (1, 1),
        'C3': (-1, 0), 'C4': (1, 0),
        'P3': (-1, -1), 'P4': (1, -1)
    }
    
    # Electrode colors
    electrode_colors = {
        'F3': '#ff7f0e', 'F4': '#1f77b4',
        'C3': '#2ca02c', 'C4': '#d62728',
        'P3': '#9467bd', 'P4': '#8c564b',
    }
    
    # Get edge weights for width scaling
    edge_weights = [G[u][v]['weight'] * 5000 for u, v in G.edges()]
    
    # Draw nodes with custom colors
    node_colors = [electrode_colors.get(node, '#333333') for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_size=1500, node_color=node_colors, alpha=0.8)
    
    # Draw edges with varying width based on weight
    nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.6, 
                          arrowsize=20, arrowstyle='->')
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold')
    
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close() 