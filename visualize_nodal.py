import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os


def plot_nodal_metrics(nodal_metrics, title, output_path, scales=None):
    """Plot bar charts of nodal metrics with optional consistent scaling

    Args:
        nodal_metrics: Dictionary of nodal metrics
        title: Title for the plot
        output_path: Path to save the plot
        scales: Optional dictionary with scaling ranges:
                {'in_strength': (min, max), 'out_strength': (min, max), 'causal_flow': (min, max)}
    """
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(
        {
            "Electrode": list(nodal_metrics.keys()),
            "In-Strength": [
                metrics["in_strength"] for metrics in nodal_metrics.values()
            ],
            "Out-Strength": [
                metrics["out_strength"] for metrics in nodal_metrics.values()
            ],
            "Causal Flow": [
                metrics["causal_flow"] for metrics in nodal_metrics.values()
            ],
            "Category": [metrics["category"] for metrics in nodal_metrics.values()],
        }
    )

    # Sort by causal flow
    df = df.sort_values("Causal Flow", ascending=False)

    # Create a color map for categories
    category_colors = {
        "sender": "#2ca02c",  # Green
        "receiver": "#d62728",  # Red
        "neutral": "#7f7f7f",  # Gray
    }
    bar_colors = [category_colors[cat] for cat in df["Category"]]

    # Create subplot figure
    fig, axs = plt.subplots(3, 1, figsize=(12, 15))

    # Plot In-Strength
    sns.barplot(x="Electrode", y="In-Strength", data=df, ax=axs[0])
    axs[0].set_title("In-Strength (Incoming Influence)", fontsize=14)
    axs[0].set_xlabel("")
    if scales and "in_strength" in scales:
        axs[0].set_ylim(scales["in_strength"])
        axs[0].text(
            0.98,
            0.98,
            f"Scale: {scales['in_strength'][0]:.4f} to {scales['in_strength'][1]:.4f}",
            transform=axs[0].transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    # Plot Out-Strength
    sns.barplot(x="Electrode", y="Out-Strength", data=df, ax=axs[1])
    axs[1].set_title("Out-Strength (Outgoing Influence)", fontsize=14)
    axs[1].set_xlabel("")
    if scales and "out_strength" in scales:
        axs[1].set_ylim(scales["out_strength"])
        axs[1].text(
            0.98,
            0.98,
            f"Scale: {scales['out_strength'][0]:.4f} to {scales['out_strength'][1]:.4f}",
            transform=axs[1].transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    # Plot Causal Flow
    bars = axs[2].bar(df["Electrode"], df["Causal Flow"], color=bar_colors)
    axs[2].set_title("Causal Flow (Out-Strength minus In-Strength)", fontsize=14)
    axs[2].axhline(0, color="black", linestyle="-", alpha=0.3)
    if scales and "causal_flow" in scales:
        axs[2].set_ylim(scales["causal_flow"])
        axs[2].text(
            0.98,
            0.98,
            f"Scale: {scales['causal_flow'][0]:.4f} to {scales['causal_flow'][1]:.4f}",
            transform=axs[2].transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    # Add category labels to the bars
    for i, (_, row) in enumerate(df.iterrows()):
        axs[2].text(
            i,
            row["Causal Flow"] + (0.0001 if row["Causal Flow"] >= 0 else -0.0002),
            row["Category"],
            ha="center",
        )

    # Set super title
    plt.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust for super title

    plt.savefig(output_path, dpi=300)
    plt.close()
