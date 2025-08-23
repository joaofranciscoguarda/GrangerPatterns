import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import numpy as np


def plot_global_metrics(
    global_metrics,
    title="Global Granger Causality Metrics",
    output_path=None,
    strength_scale=None,
    density_scale=None,
):
    """
    Visualize global Granger causality metrics using bar plots with separate scaling for different metric types.

    Args:
        global_metrics (dict): Dictionary containing global metrics.
        title (str): Title for the plot.
        output_path (str, optional): Path to save the visualization. If None, the plot is displayed.
        strength_scale (tuple, optional): Optional (min, max) tuple for Granger causality strength metrics.
        density_scale (tuple, optional): Optional (min, max) tuple for network density metrics.
    """
    # Create a DataFrame from the global metrics
    data = []

    # Check if the input is in the expected format
    if not isinstance(global_metrics, dict):
        raise ValueError("global_metrics must be a dictionary")

    # Check if this is a nested structure or a flat dictionary
    any_dict_values = any(isinstance(value, dict) for value in global_metrics.values())

    if any_dict_values:
        # This is the nested format (Category -> Metrics -> Values)
        for category, metrics in global_metrics.items():
            if isinstance(metrics, dict):
                for metric_name, value in metrics.items():
                    data.append(
                        {"Category": category, "Metric": metric_name, "Value": value}
                    )
            else:
                # Handle case where the value itself is not a dict
                data.append({"Category": "All", "Metric": category, "Value": metrics})
    else:
        # This is a flat format (Metric -> Value)
        for metric_name, value in global_metrics.items():
            data.append({"Category": "All", "Metric": metric_name, "Value": value})

    df = pd.DataFrame(data)

    # Set up the figure and axes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Filter metrics for each plot
    granger_metrics = df[df["Metric"].str.contains("strength")]
    density_metrics = df[df["Metric"].str.contains("density")]

    # Check if we have any data
    if len(granger_metrics) == 0 and len(density_metrics) == 0:
        # If we don't have appropriate strength or density metrics,
        # just plot all the metrics in a single bar plot
        fig = plt.figure(figsize=(12, 8))
        sns.barplot(x="Metric", y="Value", data=df)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
    else:
        # Plot Granger causality strength metrics
        if len(granger_metrics) > 0:
            sns.barplot(
                x="Metric",
                y="Value",
                hue=(
                    "Category"
                    if "Category" in granger_metrics.columns
                    and len(granger_metrics["Category"].unique()) > 1
                    else None
                ),
                data=granger_metrics,
                ax=ax1,
            )
            ax1.set_title("Granger Causality Strength")
            ax1.set_ylabel("Strength")
            ax1.set_xlabel("")
            ax1.tick_params(axis="x", rotation=45)
        else:
            ax1.set_visible(False)

        # Plot network density metrics
        if len(density_metrics) > 0:
            sns.barplot(
                x="Metric",
                y="Value",
                hue=(
                    "Category"
                    if "Category" in density_metrics.columns
                    and len(density_metrics["Category"].unique()) > 1
                    else None
                ),
                data=density_metrics,
                ax=ax2,
            )
            ax2.set_title("Network Density")
            ax2.set_ylabel("Density")
            ax2.set_xlabel("")
            ax2.tick_params(axis="x", rotation=45)
        else:
            ax2.set_visible(False)

        # Apply separate scaling for different metric types
        if strength_scale is not None and len(granger_metrics) > 0:
            ax1.set_ylim(strength_scale)
            # Add scale information to the plot
            ax1.text(
                0.98,
                0.98,
                f"Strength Scale: {strength_scale[0]:.6f} to {strength_scale[1]:.6f}",
                transform=ax1.transAxes,
                fontsize=8,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
            )

        if density_scale is not None and len(density_metrics) > 0:
            ax2.set_ylim(density_scale)
            # Add scale information to the plot
            ax2.text(
                0.98,
                0.98,
                f"Density Scale: {density_scale[0]:.6f} to {density_scale[1]:.6f}",
                transform=ax2.transAxes,
                fontsize=8,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8),
            )

        # Set the overall title
        fig.suptitle(title, fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Save or display the plot
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    else:
        plt.show()

    plt.close()
