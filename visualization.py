import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
import pandas as pd
import os
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.colors as mcolors

class GrangerCausalityVisualizer:
    def __init__(self, output_dir='output'):
        """
        Initialize visualizer with output directory
        
        Args:
            output_dir (str): Directory for saving figures
        """
        self.figures_dir = os.path.join(output_dir, 'figures')
        Path(self.figures_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up plotting styles
        plt.style.use('seaborn-v0_8-whitegrid')
        self.electrode_colors = {
            'F3': '#ff7f0e', 'F4': '#1f77b4',
            'C3': '#2ca02c', 'C4': '#d62728',
            'P3': '#9467bd', 'P4': '#8c564b',
        }
        
    def plot_connectivity_matrix(self, gc_matrix, title, filename):
        """
        Plot a Granger Causality connectivity matrix as a heatmap
        
        Args:
            gc_matrix (pandas.DataFrame): GC matrix
            title (str): Plot title
            filename (str): Output filename
        """
        plt.figure(figsize=(10, 8))
        mask = np.eye(len(gc_matrix))
        sns.heatmap(gc_matrix, annot=True, fmt=".6f", cmap='viridis', 
                    mask=mask, square=True, linewidths=.5)
        plt.title(f"{title}\nGranger Causality Matrix", fontsize=14)
        plt.xlabel('Target Electrode', fontsize=12)
        plt.ylabel('Source Electrode', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, f"{filename}_matrix.png"), dpi=300)
        plt.close()
        
        # Create interactive Plotly version
        fig = go.Figure(data=go.Heatmap(
            z=gc_matrix.values,
            x=gc_matrix.columns,
            y=gc_matrix.index,
            colorscale='Viridis',
            text=np.round(gc_matrix.values, 6),
            hovertemplate='Source: %{y}<br>Target: %{x}<br>GC Value: %{text}<extra></extra>',
            colorbar=dict(title='GC Strength')
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{title}<br>Granger Causality Matrix",
            width=800,
            height=700,
            xaxis=dict(title='Target Electrode', tickangle=0),
            yaxis=dict(title='Source Electrode')
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.figures_dir, f"{filename}_matrix_interactive.html"))
    
    def plot_network_graph(self, G, title, filename):
        """
        Plot a network graph of Granger Causality
        
        Args:
            G (networkx.DiGraph): NetworkX directed graph
            title (str): Plot title
            filename (str): Output filename
        """
        plt.figure(figsize=(12, 10))
        pos = {
            'F3': (-1, 1), 'F4': (1, 1),
            'C3': (-1, 0), 'C4': (1, 0),
            'P3': (-1, -1), 'P4': (1, -1)
        }
        edge_weights = [G[u][v]['weight'] * 5000 for u, v in G.edges()]
        node_colors = [self.electrode_colors.get(node, '#333333') for node in G.nodes()]
        
        nx.draw_networkx_nodes(G, pos, node_size=1500, node_color=node_colors)
        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.6, 
                              arrowsize=20, arrowstyle='->')
        nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold')
        
        plt.title(title, fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, f"{filename}_network.png"), dpi=300)
        plt.close()
        
        # Create interactive network graph with Plotly
        edge_x = []
        edge_y = []
        edge_traces = []
        
        # Create edge traces with arrows
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            weight = G[edge[0]][edge[1]]['weight']
            
            # Create arrow representation
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=weight*5000, color='#888'),
                hoverinfo='text',
                text=f"{edge[0]} → {edge[1]}: {weight:.6f}",
                mode='lines+markers',
                marker=dict(
                    symbol='arrow',
                    size=15,
                    color='#888',
                    angleref='previous'
                )
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_colors.append(self.electrode_colors.get(node, '#333333'))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            textfont=dict(size=15, color='black'),
            marker=dict(
                size=30,
                color=node_colors,
                line_width=2,
                line=dict(color='white')
            ),
            hoverinfo='text'
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # Set layout
        fig.update_layout(
            title=title,
            showlegend=False,
            width=800,
            height=800,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.figures_dir, f"{filename}_network_interactive.html"))
    
    def plot_nodal_metrics(self, nodal_metrics, title, filename):
        """
        Plot bar charts of nodal metrics
        
        Args:
            nodal_metrics (dict): Dictionary of nodal metrics
            title (str): Plot title
            filename (str): Output filename
        """
        df = pd.DataFrame({
            'Electrode': list(nodal_metrics.keys()),
            'In-Strength': [metrics['in_strength'] for metrics in nodal_metrics.values()],
            'Out-Strength': [metrics['out_strength'] for metrics in nodal_metrics.values()],
            'Causal Flow': [metrics['causal_flow'] for metrics in nodal_metrics.values()],
            'Category': [metrics['category'] for metrics in nodal_metrics.values()]
        })
        
        df = df.sort_values('Causal Flow', ascending=False)
        category_colors = {
            'sender': '#2ca02c', 'receiver': '#d62728', 'neutral': '#7f7f7f'
        }
        
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        sns.barplot(x='Electrode', y='In-Strength', data=df, ax=axs[0])
        axs[0].set_title('In-Strength (Incoming Influence)', fontsize=14)
        
        sns.barplot(x='Electrode', y='Out-Strength', data=df, ax=axs[1])
        axs[1].set_title('Out-Strength (Outgoing Influence)', fontsize=14)
        
        axs[2].bar(df['Electrode'], df['Causal Flow'], 
                 color=[category_colors[cat] for cat in df['Category']])
        axs[2].axhline(0, color='black', linestyle='-', alpha=0.3)
        axs[2].set_title('Causal Flow', fontsize=14)
        
        plt.suptitle(title, fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.savefig(os.path.join(self.figures_dir, f"{filename}_nodal_metrics.png"), dpi=300)
        plt.close()
        
        # Create interactive Plotly version
        fig = make_subplots(rows=3, cols=1, 
                          subplot_titles=('In-Strength (Incoming Influence)', 
                                         'Out-Strength (Outgoing Influence)', 
                                         'Causal Flow'))
        
        # Add in-strength trace
        fig.add_trace(
            go.Bar(
                x=df['Electrode'], 
                y=df['In-Strength'],
                marker_color=[self.electrode_colors.get(e, '#333333') for e in df['Electrode']],
                text=df['In-Strength'].round(6),
                hovertemplate='Electrode: %{x}<br>In-Strength: %{text}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add out-strength trace
        fig.add_trace(
            go.Bar(
                x=df['Electrode'], 
                y=df['Out-Strength'],
                marker_color=[self.electrode_colors.get(e, '#333333') for e in df['Electrode']],
                text=df['Out-Strength'].round(6),
                hovertemplate='Electrode: %{x}<br>Out-Strength: %{text}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add causal flow trace
        fig.add_trace(
            go.Bar(
                x=df['Electrode'], 
                y=df['Causal Flow'],
                marker_color=[category_colors[cat] for cat in df['Category']],
                text=df['Category'],
                hovertemplate='Electrode: %{x}<br>Causal Flow: %{y:.6f}<br>Category: %{text}<extra></extra>'
            ),
            row=3, col=1
        )
        
        # Add a horizontal line at y=0 for causal flow
        fig.add_shape(
            type="line",
            x0=-0.5, 
            x1=len(df)-0.5,
            y0=0, 
            y1=0,
            line=dict(color="black", width=1, dash="solid"),
            row=3, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=900,
            width=800,
            showlegend=False
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.figures_dir, f"{filename}_nodal_metrics_interactive.html"))
    
    def plot_pairwise_comparison(self, pairwise_data, title, filename):
        """
        Plot pairwise connection strengths
        
        Args:
            pairwise_data (dict): Dictionary of pairwise connections
            title (str): Plot title
            filename (str): Output filename
        """
        df = pd.DataFrame({
            'Pair': list(pairwise_data['directional_pairs'].keys()),
            'GC Value': list(pairwise_data['directional_pairs'].values())
        })
        df[['Source', 'Target']] = df['Pair'].str.split('→', expand=True)
        df = df.sort_values('GC Value', ascending=False)
        
        plt.figure(figsize=(14, 10))
        plt.bar(df['Pair'], df['GC Value'], 
               color=[self.electrode_colors.get(src, '#333333') for src in df['Source']])
        plt.title(title, fontsize=16)
        plt.xlabel('Connection (Source → Target)', fontsize=14)
        plt.ylabel('Granger Causality Value', fontsize=14)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, f"{filename}_pairwise.png"), dpi=300)
        plt.close()
        
        # Create interactive Plotly version
        fig = px.bar(
            df, 
            x='Pair', 
            y='GC Value',
            color='Source',
            color_discrete_map=self.electrode_colors,
            hover_data=['Source', 'Target', 'GC Value'],
            title=title
        )
        
        fig.update_layout(
            xaxis_title='Connection (Source → Target)',
            yaxis_title='Granger Causality Value',
            xaxis_tickangle=-90,
            height=700,
            width=1000
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.figures_dir, f"{filename}_pairwise_interactive.html"))
    
    def plot_global_metrics(self, global_metrics, title, filename):
        """
        Plot global GC metrics
        
        Args:
            global_metrics (dict): Dictionary of global metrics
            title (str): Plot title
            filename (str): Output filename
        """
        metrics_to_plot = ['global_gc_strength', 'mean_gc_strength', 
                          'network_density_th0.0001', 'network_density_th0.0005']
        
        metric_names = {
            'global_gc_strength': 'Global GC Strength',
            'mean_gc_strength': 'Mean GC Strength',
            'network_density_th0.0001': 'Network Density (th=0.0001)',
            'network_density_th0.0005': 'Network Density (th=0.0005)',
        }
        
        data = {metric_names[m]: global_metrics[m] for m in metrics_to_plot if m in global_metrics}
        df = pd.DataFrame({'Metric': list(data.keys()), 'Value': list(data.values())})
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Metric', y='Value', data=df)
        plt.title(title, fontsize=16)
        plt.xlabel('')
        plt.ylabel('Value', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, f"{filename}_global_metrics.png"), dpi=300)
        plt.close()
        
        # Create interactive Plotly version
        fig = make_subplots(rows=1, cols=1, 
                          subplot_titles=('Granger Causality Strength Metrics'))
        
        # Add GC strength trace
        fig.add_trace(
            go.Bar(
                x=df['Metric'], 
                y=df['Value'],
                marker_color=px.colors.qualitative.Plotly[:len(df)],
                text=df['Value'].round(6),
                hovertemplate='Metric: %{x}<br>Value: %{text}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=600,
            width=800,
            showlegend=False
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.figures_dir, f"{filename}_global_metrics_interactive.html"))

# Create output directory
def create_output_dirs(base_dir='output'):
    """Create output directories for figures and reports"""
    figures_dir = os.path.join(base_dir, 'figures')
    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    return figures_dir

# Matrix plot
def plot_matrix(gc_matrix, title, filename, output_dir):
    """Plot GC matrix as heatmap"""
    plt.figure(figsize=(10, 8))
    mask = np.eye(len(gc_matrix))
    sns.heatmap(gc_matrix, annot=True, fmt=".6f", cmap='viridis', mask=mask)
    plt.title(title)
    plt.xlabel('Target')
    plt.ylabel('Source')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

# Network plot
def plot_network(gc_matrix, title, filename, output_dir, threshold=0.0005):
    """Plot network graph from GC matrix"""
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for electrode in gc_matrix.index:
        G.add_node(electrode)
    
    # Add edges
    for source in gc_matrix.index:
        for target in gc_matrix.columns:
            if source != target and gc_matrix.loc[source, target] > threshold:
                G.add_edge(source, target, weight=gc_matrix.loc[source, target])
    
    # EEG electrode positions
    pos = {
        'F3': (-1, 1), 'F4': (1, 1),
        'C3': (-1, 0), 'C4': (1, 0),
        'P3': (-1, -1), 'P4': (1, -1)
    }
    
    # Plot
    plt.figure(figsize=(10, 8))
    
    # Edge weights for width
    edge_weights = [G[u][v]['weight'] * 5000 for u, v in G.edges()]
    
    # Draw network
    nx.draw_networkx_nodes(G, pos, node_size=1000)
    nx.draw_networkx_edges(G, pos, width=edge_weights, arrowstyle='->')
    nx.draw_networkx_labels(G, pos, font_weight='bold')
    
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()
    
    return G

# Nodal metrics plot
def plot_nodal_metrics(nodal_metrics, title, filename, output_dir):
    """Plot nodal metrics"""
    # Create DataFrame
    df = pd.DataFrame({
        'Electrode': list(nodal_metrics.keys()),
        'In-Strength': [m['in_strength'] for m in nodal_metrics.values()],
        'Out-Strength': [m['out_strength'] for m in nodal_metrics.values()],
        'Causal Flow': [m['causal_flow'] for m in nodal_metrics.values()],
        'Category': [m['category'] for m in nodal_metrics.values()]
    })
    
    # Sort by causal flow
    df = df.sort_values('Causal Flow', ascending=False)
    
    # Plot
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    
    # In-strength
    sns.barplot(x='Electrode', y='In-Strength', data=df, ax=axs[0])
    axs[0].set_title('In-Strength')
    
    # Out-strength
    sns.barplot(x='Electrode', y='Out-Strength', data=df, ax=axs[1])
    axs[1].set_title('Out-Strength')
    
    # Causal flow
    category_colors = {'sender': 'green', 'receiver': 'red', 'neutral': 'gray'}
    bar_colors = [category_colors[cat] for cat in df['Category']]
    axs[2].bar(df['Electrode'], df['Causal Flow'], color=bar_colors)
    axs[2].axhline(0, color='black', linestyle='-', alpha=0.5)
    axs[2].set_title('Causal Flow')
    
    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

# Pairwise metrics plot
def plot_pairwise(pairwise_data, title, filename, output_dir):
    """Plot pairwise connections"""
    # Create DataFrame
    df = pd.DataFrame({
        'Pair': list(pairwise_data['directional_pairs'].keys()),
        'Value': list(pairwise_data['directional_pairs'].values())
    })
    
    # Sort by value
    df = df.sort_values('Value', ascending=False)
    
    # Plot
    plt.figure(figsize=(12, 8))
    plt.bar(df['Pair'], df['Value'])
    plt.title(title)
    plt.xlabel('Connection')
    plt.ylabel('GC Value')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

# Global metrics plot
def plot_global_metrics(global_metrics, title, filename, output_dir):
    """Plot global metrics"""
    # Select metrics to plot
    metrics = {
        'Global GC Strength': global_metrics['global_gc_strength'],
        'Mean GC Strength': global_metrics['mean_gc_strength'],
        'Network Density (th=0.0001)': global_metrics['network_density_th0.0001'],
        'Network Density (th=0.0005)': global_metrics['network_density_th0.0005']
    }
    
    # Create DataFrame
    df = pd.DataFrame({'Metric': list(metrics.keys()), 'Value': list(metrics.values())})
    
    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Metric', y='Value', data=df)
    plt.title(title)
    plt.xlabel('')
    plt.ylabel('Value')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close() 