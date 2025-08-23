#!/usr/bin/env python3
"""
Pairwise Visualization Service

This module provides functions for generating pairwise connection visualizations
with consistent scaling to prevent visual distortions.
"""

import os
import numpy as np
from visualize_pairwise import plot_pairwise_comparison


def calculate_pairwise_scales_per_participant(analyses_by_participant):
    """Calculate consistent scales for pairwise metrics per participant

    Args:
        analyses_by_participant: Dictionary with participant_id as keys and list of analyses as values

    Returns:
        Dictionary with participant scales: {participant_id: (min, max)}
    """
    participant_scales = {}

    for participant_id, analyses in analyses_by_participant.items():
        if not analyses:
            continue

        # Collect all pairwise GC values for this participant
        all_gc_values = []

        for analysis_key, analysis in analyses:
            pairwise_data = analysis["pairwise"]
            if "directional_pairs" in pairwise_data:
                all_gc_values.extend(pairwise_data["directional_pairs"].values())

        if all_gc_values:  # Only if we have data
            # Calculate scales with small padding
            gc_min, gc_max = min(all_gc_values), max(all_gc_values)

            # Add 5% padding to range
            gc_range = gc_max - gc_min
            padding = gc_range * 0.05 if gc_range > 0 else 0.0001

            participant_scales[participant_id] = (gc_min - padding, gc_max + padding)

    return participant_scales


def generate_individual_pairwise_visualizations(analyzer, output_dir):
    """Generate individual pairwise visualizations with consistent scaling per participant

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_participant

    # Group analyses by participant for consistent scaling
    analyses_by_participant = group_analyses_by_participant(analyzer)

    # Calculate scales per participant
    participant_scales = calculate_pairwise_scales_per_participant(
        analyses_by_participant
    )

    # Generate individual visualizations
    pairwise_dir = os.path.join(output_dir, "pairwise")

    for key, analysis in analyzer.analyses.items():
        participant_id = analysis["metadata"]["participant_id"]
        timepoint = analysis["metadata"]["timepoint"]
        condition = analysis["metadata"]["condition"]

        # Get scale for this participant
        scale_range = participant_scales.get(participant_id, None)

        base_name = f"{participant_id}_{timepoint}_{condition}"
        title = f"Pairwise Connections: {participant_id} {timepoint} {condition}"

        if scale_range:
            title += f" (Participant {participant_id} Scale)"

        output_path = os.path.join(pairwise_dir, f"{base_name}_pairwise.png")

        plot_pairwise_comparison(
            analysis["pairwise"], title, output_path, scale_range=scale_range
        )

        print(f"  Generated: {base_name}_pairwise.png")


def generate_condition_level_pairwise_visualizations(analyzer, output_dir):
    """Generate condition-level pairwise visualizations (averaged across participants)

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_condition

    # Group analyses by condition
    analyses_by_condition = group_analyses_by_condition(analyzer)

    # Calculate average pairwise metrics per condition
    condition_averages = {}
    for condition, analyses in analyses_by_condition.items():
        if not analyses:
            continue

        # Get all possible pairs from first analysis
        first_analysis_key, first_analysis = analyses[0]
        if "directional_pairs" not in first_analysis["pairwise"]:
            continue

        all_pairs = list(first_analysis["pairwise"]["directional_pairs"].keys())

        # Initialize accumulators for each pair
        pair_values = {pair: [] for pair in all_pairs}

        # Collect values from all analyses for this condition
        for analysis_key, analysis in analyses:
            pairwise_data = analysis["pairwise"]
            if "directional_pairs" in pairwise_data:
                for pair, value in pairwise_data["directional_pairs"].items():
                    if pair in pair_values:
                        pair_values[pair].append(value)

        # Calculate averages
        averaged_pairwise = {"directional_pairs": {}}

        for pair, values in pair_values.items():
            if values:  # Only if we have data
                averaged_pairwise["directional_pairs"][pair] = np.mean(values)

        condition_averages[condition] = averaged_pairwise

    # Calculate global scale across all conditions
    all_gc_values = []

    for condition_pairwise in condition_averages.values():
        if "directional_pairs" in condition_pairwise:
            all_gc_values.extend(condition_pairwise["directional_pairs"].values())

    if all_gc_values:
        # Calculate global scale with padding
        gc_min, gc_max = min(all_gc_values), max(all_gc_values)

        # Add 5% padding
        gc_range = gc_max - gc_min
        padding = gc_range * 0.05 if gc_range > 0 else 0.0001

        global_scale = (gc_min - padding, gc_max + padding)

        # Generate condition-level visualizations
        by_condition_dir = os.path.join(output_dir, "by_condition")

        for condition, averaged_pairwise in condition_averages.items():
            if (
                "directional_pairs" in averaged_pairwise
                and averaged_pairwise["directional_pairs"]
            ):
                title = f"Average Pairwise Connections: {condition} (n={len(analyses_by_condition[condition])} participants)"
                title += f" - Global Scale"
                output_path = os.path.join(
                    by_condition_dir, f"average_{condition}_pairwise.png"
                )

                plot_pairwise_comparison(
                    averaged_pairwise, title, output_path, scale_range=global_scale
                )

                print(f"  Generated: average_{condition}_pairwise.png")

    print(f"  Condition-level pairwise visualizations saved to: {by_condition_dir}")
