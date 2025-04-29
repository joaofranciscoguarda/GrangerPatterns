import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

def plot_nodal_metrics(nodal_metrics, title, output_path):
    """Plot bar charts of nodal metrics"""
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame({
        'Electrode': list(nodal_metrics.keys()),
        'In-Strength': [metrics['in_strength'] for metrics in nodal_metrics.values()],
        'Out-Strength': [metrics['out_strength'] for metrics in nodal_metrics.values()],
        'Causal Flow': [metrics['causal_flow'] for metrics in nodal_metrics.values()],
        'Category': [metrics['category'] for metrics in nodal_metrics.values()]
    })
    
    # Sort by causal flow
    df = df.sort_values('Causal Flow', ascending=False)
    
    # Create a color map for categories
    category_colors = {
        'sender': '#2ca02c',  # Green
        'receiver': '#d62728',  # Red
        'neutral': '#7f7f7f'   # Gray
    }
    bar_colors = [category_colors[cat] for cat in df['Category']]
    
    # Create subplot figure
    fig, axs = plt.subplots(3, 1, figsize=(12, 15))
    
    # Plot In-Strength
    sns.barplot(x='Electrode', y='In-Strength', data=df, ax=axs[0])
    axs[0].set_title('In-Strength (Incoming Influence)', fontsize=14)
    axs[0].set_xlabel('')
    
    # Plot Out-Strength
    sns.barplot(x='Electrode', y='Out-Strength', data=df, ax=axs[1])
    axs[1].set_title('Out-Strength (Outgoing Influence)', fontsize=14)
    axs[1].set_xlabel('')
    
    # Plot Causal Flow
    bars = axs[2].bar(df['Electrode'], df['Causal Flow'], color=bar_colors)
    axs[2].set_title('Causal Flow (Out-Strength minus In-Strength)', fontsize=14)
    axs[2].axhline(0, color='black', linestyle='-', alpha=0.3)
    
    # Add category labels to the bars
    for i, (_, row) in enumerate(df.iterrows()):
        axs[2].text(i, row['Causal Flow'] + (0.0001 if row['Causal Flow'] >= 0 else -0.0002), 
                  row['Category'], ha='center')
    
    # Set super title
    plt.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust for super title
    
    plt.savefig(output_path, dpi=300)
    plt.close() 