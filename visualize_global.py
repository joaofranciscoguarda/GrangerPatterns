import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import numpy as np

def plot_global_metrics(global_metrics, title='Global Granger Causality Metrics', output_path=None):
    """
    Visualize global Granger causality metrics using bar plots.
    
    Args:
        global_metrics (dict): Dictionary containing global metrics with categories as keys.
        title (str): Title for the plot.
        output_path (str, optional): Path to save the visualization. If None, the plot is displayed.
    """
    # Create a DataFrame from the global metrics
    data = []
    for category, metrics in global_metrics.items():
        for metric_name, value in metrics.items():
            data.append({'Category': category, 'Metric': metric_name, 'Value': value})
    
    df = pd.DataFrame(data)
    
    # Set up the figure and axes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Filter metrics for each plot
    granger_metrics = df[df['Metric'].str.contains('strength')]
    density_metrics = df[df['Metric'].str.contains('density')]
    
    # Plot Granger causality strength metrics
    sns.barplot(
        x='Category', 
        y='Value', 
        hue='Category',  # Added hue parameter
        data=granger_metrics, 
        ax=ax1,
        dodge=False     # Set dodge to False since we're using the same variable
    )
    ax1.set_title('Granger Causality Strength')
    ax1.set_ylabel('Strength')
    ax1.set_xlabel('')
    
    # Plot network density metrics
    sns.barplot(
        x='Category', 
        y='Value', 
        hue='Category',  # Added hue parameter
        data=density_metrics, 
        ax=ax2,
        dodge=False     # Set dodge to False since we're using the same variable
    )
    ax2.set_title('Network Density')
    ax2.set_ylabel('Density')
    ax2.set_xlabel('')
    
    # Set the overall title
    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save or display the plot
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close() 