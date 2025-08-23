import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os


def plot_connectivity_matrix(gc_matrix, title, output_path, vmin=None, vmax=None):
    """Plot a Granger Causality connectivity matrix as a heatmap"""
    plt.figure(figsize=(10, 8))

    # Create a mask for the diagonal
    mask = np.eye(len(gc_matrix))

    # Create heatmap with optional vmin/vmax for consistent scaling
    sns.heatmap(
        gc_matrix,
        annot=True,
        fmt=".6f",
        cmap="viridis",
        mask=mask,
        square=True,
        linewidths=0.5,
        vmin=vmin,
        vmax=vmax,
    )

    plt.title(f"{title}\nGranger Causality Matrix (Source → Target)", fontsize=14)
    plt.xlabel("Target Electrode", fontsize=12)
    plt.ylabel("Source Electrode", fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
