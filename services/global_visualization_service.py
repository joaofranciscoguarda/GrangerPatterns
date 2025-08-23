#!/usr/bin/env python3
"""
Global Visualization Service

This module provides functions for generating global metric visualizations
with consistent scaling to prevent visual distortions.
"""

import os
import numpy as np
from visualize_global import plot_global_metrics


def calculate_global_scales_per_participant(analyses_by_participant):
    """Calculate consistent scales for global metrics per participant, separated by metric type

    Args:
        analyses_by_participant: Dictionary with participant_id as keys and list of analyses as values

    Returns:
        Dictionary with participant scales: {participant_id: {'strength': (min, max), 'density': (min, max)}}
    """
    participant_scales = {}

    for participant_id, analyses in analyses_by_participant.items():
        if not analyses:
            continue

        # Collect strength and density metrics separately
        strength_values = []
        density_values = []

        for analysis_key, analysis in analyses:
            global_data = analysis["global"]
            if isinstance(global_data, dict):
                # Separate strength and density metrics
                for key, value in global_data.items():
                    if isinstance(value, dict):
                        for metric_name, metric_value in value.items():
                            if "strength" in metric_name.lower():
                                strength_values.append(metric_value)
                            elif "density" in metric_name.lower():
                                density_values.append(metric_value)
                    else:
                        # Check if the key itself indicates the type
                        if "strength" in key.lower():
                            strength_values.append(value)
                        elif "density" in key.lower():
                            density_values.append(value)
            else:
                # Single value - assume it's a strength metric
                strength_values.append(global_data)

        participant_scales[participant_id] = {}

        # Calculate strength scale
        if strength_values:
            strength_min, strength_max = min(strength_values), max(strength_values)
            strength_range = strength_max - strength_min
            strength_padding = strength_range * 0.05 if strength_range > 0 else 0.0001
            participant_scales[participant_id]["strength"] = (
                strength_min - strength_padding,
                strength_max + strength_padding,
            )

        # Calculate density scale
        if density_values:
            density_min, density_max = min(density_values), max(density_values)
            density_range = density_max - density_min
            density_padding = density_range * 0.05 if density_range > 0 else 0.0001
            participant_scales[participant_id]["density"] = (
                density_min - density_padding,
                density_max + density_padding,
            )

    return participant_scales


def generate_individual_global_visualizations(analyzer, output_dir):
    """Generate individual global metric visualizations with consistent scaling per participant

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_participant

    # Group analyses by participant for consistent scaling
    analyses_by_participant = group_analyses_by_participant(analyzer)

    # Calculate scales per participant
    participant_scales = calculate_global_scales_per_participant(
        analyses_by_participant
    )

    # Generate individual visualizations
    global_dir = os.path.join(output_dir, "global")

    for key, analysis in analyzer.analyses.items():
        participant_id = analysis["metadata"]["participant_id"]
        timepoint = analysis["metadata"]["timepoint"]
        condition = analysis["metadata"]["condition"]

        # Get scales for this participant
        participant_scale = participant_scales.get(participant_id, {})
        strength_scale = participant_scale.get("strength", None)
        density_scale = participant_scale.get("density", None)

        base_name = f"{participant_id}_{timepoint}_{condition}"
        title = f"Global Metrics: {participant_id} {timepoint} {condition}"

        if strength_scale or density_scale:
            title += f" (Participant {participant_id} Scales)"

        output_path = os.path.join(global_dir, f"{base_name}_global.png")

        plot_global_metrics(
            analysis["global"],
            title,
            output_path,
            strength_scale=strength_scale,
            density_scale=density_scale,
        )

        print(f"  Generated: {base_name}_global.png")


def generate_condition_level_global_visualizations(analyzer, output_dir):
    """Generate condition-level global metric visualizations (averaged across participants)

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_condition

    # Group analyses by condition
    analyses_by_condition = group_analyses_by_condition(analyzer)

    # Calculate average global metrics per condition
    condition_averages = {}
    for condition, analyses in analyses_by_condition.items():
        if not analyses:
            continue

        # Get all possible metrics from first analysis
        first_analysis_key, first_analysis = analyses[0]
        if "global" not in first_analysis:
            continue

        first_global = first_analysis["global"]

        # Initialize structure for averaging
        if isinstance(first_global, dict):
            # Check if nested structure
            any_dict_values = any(
                isinstance(value, dict) for value in first_global.values()
            )

            if any_dict_values:
                # Nested structure: Category -> Metrics -> Values
                averaged_global = {}
                for category, metrics in first_global.items():
                    if isinstance(metrics, dict):
                        averaged_global[category] = {}
                        for metric_name in metrics.keys():
                            # Collect values for this metric across all analyses
                            metric_values = []
                            for analysis_key, analysis in analyses:
                                if (
                                    "global" in analysis
                                    and category in analysis["global"]
                                    and isinstance(analysis["global"][category], dict)
                                    and metric_name in analysis["global"][category]
                                ):
                                    metric_values.append(
                                        analysis["global"][category][metric_name]
                                    )

                            if metric_values:
                                averaged_global[category][metric_name] = np.mean(
                                    metric_values
                                )
                    else:
                        # Handle case where category value is not a dict
                        metric_values = []
                        for analysis_key, analysis in analyses:
                            if "global" in analysis and category in analysis["global"]:
                                metric_values.append(analysis["global"][category])

                        if metric_values:
                            averaged_global[category] = np.mean(metric_values)
            else:
                # Flat structure: Metric -> Value
                averaged_global = {}
                for metric_name in first_global.keys():
                    metric_values = []
                    for analysis_key, analysis in analyses:
                        if "global" in analysis and metric_name in analysis["global"]:
                            metric_values.append(analysis["global"][metric_name])

                    if metric_values:
                        averaged_global[metric_name] = np.mean(metric_values)
        else:
            # Single value structure
            metric_values = []
            for analysis_key, analysis in analyses:
                if "global" in analysis:
                    metric_values.append(analysis["global"])

            if metric_values:
                averaged_global = np.mean(metric_values)
            else:
                averaged_global = {}

        condition_averages[condition] = averaged_global

    # Calculate separate global scales for strength and density metrics
    all_strength_values = []
    all_density_values = []

    for condition_global in condition_averages.values():
        if isinstance(condition_global, dict):
            # Separate strength and density metrics
            for key, value in condition_global.items():
                if isinstance(value, dict):
                    for metric_name, metric_value in value.items():
                        if "strength" in metric_name.lower():
                            all_strength_values.append(metric_value)
                        elif "density" in metric_name.lower():
                            all_density_values.append(metric_value)
                else:
                    # Check if the key itself indicates the type
                    if "strength" in key.lower():
                        all_strength_values.append(value)
                    elif "density" in key.lower():
                        all_density_values.append(value)
        else:
            # Single value - assume it's a strength metric
            all_strength_values.append(condition_global)

    # Calculate strength scale
    strength_scale = None
    if all_strength_values:
        strength_min, strength_max = min(all_strength_values), max(all_strength_values)
        strength_range = strength_max - strength_min
        strength_padding = strength_range * 0.05 if strength_range > 0 else 0.0001
        strength_scale = (
            strength_min - strength_padding,
            strength_max + strength_padding,
        )

    # Calculate density scale
    density_scale = None
    if all_density_values:
        density_min, density_max = min(all_density_values), max(all_density_values)
        density_range = density_max - density_min
        density_padding = density_range * 0.05 if density_range > 0 else 0.0001
        density_scale = (density_min - density_padding, density_max + density_padding)

        # Generate condition-level visualizations
        by_condition_dir = os.path.join(output_dir, "by_condition")

        for condition, averaged_global in condition_averages.items():
            if averaged_global and (
                strength_scale or density_scale
            ):  # Only if we have data and scales
                title = f"Average Global Metrics: {condition} (n={len(analyses_by_condition[condition])} participants)"
                title += f" - Separate Scales"
                output_path = os.path.join(
                    by_condition_dir, f"average_{condition}_global.png"
                )

                plot_global_metrics(
                    averaged_global,
                    title,
                    output_path,
                    strength_scale=strength_scale,
                    density_scale=density_scale,
                )

                print(f"  Generated: average_{condition}_global.png")

    print(f"  Condition-level global visualizations saved to: {by_condition_dir}")
