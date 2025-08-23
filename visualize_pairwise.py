import matplotlib.pyplot as plt
import pandas as pd
import os


def plot_pairwise_comparison(
    pairwise_data, title=None, output_path=None, scale_range=None
):
    """Plot pairwise connection strengths with optional consistent scaling

    Args:
        pairwise_data: Dictionary containing pairwise connection data
        title: Title for the plot
        output_path: Path to save the plot
        scale_range: Optional tuple (min, max) for consistent y-axis scaling
    """
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(
        {
            "Pair": list(pairwise_data["directional_pairs"].keys()),
            "GC Value": list(pairwise_data["directional_pairs"].values()),
        }
    )

    # Extract source and target from pair
    df[["Source", "Target"]] = df["Pair"].str.split("→", expand=True)

    # Electrode colors
    electrode_colors = {
        "F3": "#ff7f0e",
        "F4": "#1f77b4",
        "C3": "#2ca02c",
        "C4": "#d62728",
        "P3": "#9467bd",
        "P4": "#8c564b",
    }

    # Sort by GC value
    df = df.sort_values("GC Value", ascending=False)

    # Create a figure
    plt.figure(figsize=(14, 10))

    # Plot bar chart with each bar colored by source electrode
    bars = plt.bar(
        df["Pair"],
        df["GC Value"],
        color=[electrode_colors.get(src, "#333333") for src in df["Source"]],
    )

    # Apply consistent scaling if provided
    if scale_range is not None:
        plt.ylim(scale_range)
        # Add scale information to the plot
        plt.text(
            0.02,
            0.98,
            f"Scale: {scale_range[0]:.6f} to {scale_range[1]:.6f}",
            transform=plt.gca().transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    # Add labels
    if title:
        plt.title(title, fontsize=16)
    plt.xlabel("Connection (Source → Target)", fontsize=14)
    plt.ylabel("Granger Causality Value", fontsize=14)
    plt.xticks(rotation=90)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Create a legend for electrode colors
    unique_sources = df["Source"].unique()
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=electrode_colors.get(src, "#333333"))
        for src in unique_sources
    ]
    plt.legend(legend_handles, unique_sources, title="Source Electrode")

    plt.tight_layout()

    # Save or show the figure
    if output_path:
        plt.savefig(output_path, dpi=300)
        plt.close()
    else:
        plt.show()
