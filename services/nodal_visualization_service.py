#!/usr/bin/env python3
"""
Nodal Visualization Service

This module provides functions for generating nodal metric visualizations
with consistent scaling to prevent visual distortions.
"""

import os
import numpy as np
from visualize_nodal import plot_nodal_metrics


def calculate_nodal_scales_per_participant(analyses_by_participant):
    """Calculate consistent scales for nodal metrics per participant

    Args:
        analyses_by_participant: Dictionary with participant_id as keys and list of analyses as values

    Returns:
        Dictionary with participant scales: {participant_id: scales_dict}
    """
    participant_scales = {}

    for participant_id, analyses in analyses_by_participant.items():
        if not analyses:
            continue

        # Collect all nodal metric values for this participant
        all_in_strength = []
        all_out_strength = []
        all_causal_flow = []

        for analysis_key, analysis in analyses:
            nodal_metrics = analysis["nodal"]
            for electrode, metrics in nodal_metrics.items():
                all_in_strength.append(metrics["in_strength"])
                all_out_strength.append(metrics["out_strength"])
                all_causal_flow.append(metrics["causal_flow"])

        if all_in_strength:  # Only if we have data
            # Calculate scales with small padding
            in_min, in_max = min(all_in_strength), max(all_in_strength)
            out_min, out_max = min(all_out_strength), max(all_out_strength)
            flow_min, flow_max = min(all_causal_flow), max(all_causal_flow)

            # Add 5% padding to ranges
            in_range = in_max - in_min
            out_range = out_max - out_min
            flow_range = flow_max - flow_min

            padding_in = in_range * 0.05 if in_range > 0 else 0.0001
            padding_out = out_range * 0.05 if out_range > 0 else 0.0001
            padding_flow = flow_range * 0.05 if flow_range > 0 else 0.0001

            participant_scales[participant_id] = {
                "in_strength": (in_min - padding_in, in_max + padding_in),
                "out_strength": (out_min - padding_out, out_max + padding_out),
                "causal_flow": (flow_min - padding_flow, flow_max + padding_flow),
            }

    return participant_scales


def generate_individual_nodal_visualizations(analyzer, output_dir):
    """Generate individual nodal visualizations with consistent scaling per participant

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_participant

    # Group analyses by participant for consistent scaling
    analyses_by_participant = group_analyses_by_participant(analyzer)

    # Calculate scales per participant
    participant_scales = calculate_nodal_scales_per_participant(analyses_by_participant)

    # Generate individual visualizations
    nodals_dir = os.path.join(output_dir, "nodals")

    for key, analysis in analyzer.analyses.items():
        participant_id = analysis["metadata"]["participant_id"]
        timepoint = analysis["metadata"]["timepoint"]
        condition = analysis["metadata"]["condition"]

        # Get scales for this participant
        scales = participant_scales.get(participant_id, None)

        base_name = f"{participant_id}_{timepoint}_{condition}"
        title = f"Nodal Metrics: {participant_id} {timepoint} {condition}"

        if scales:
            title += f" (Participant {participant_id} Scale)"

        output_path = os.path.join(nodals_dir, f"{base_name}_nodal.png")

        plot_nodal_metrics(analysis["nodal"], title, output_path, scales=scales)

        print(f"  Generated: {base_name}_nodal.png")


def generate_condition_level_nodal_visualizations(analyzer, output_dir):
    """Generate condition-level nodal visualizations (averaged across participants)

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
    """
    from .data_loader_service import group_analyses_by_condition

    # Group analyses by condition
    analyses_by_condition = group_analyses_by_condition(analyzer)

    # Calculate average nodal metrics per condition
    condition_averages = {}
    for condition, analyses in analyses_by_condition.items():
        if not analyses:
            continue

        # Get all electrodes from first analysis
        first_analysis_key, first_analysis = analyses[0]
        electrodes = list(first_analysis["nodal"].keys())

        # Initialize accumulators
        electrode_metrics = {
            electrode: {"in_strength": [], "out_strength": [], "causal_flow": []}
            for electrode in electrodes
        }

        # Collect metrics from all analyses for this condition
        for analysis_key, analysis in analyses:
            for electrode in electrodes:
                if electrode in analysis["nodal"]:
                    metrics = analysis["nodal"][electrode]
                    electrode_metrics[electrode]["in_strength"].append(
                        metrics["in_strength"]
                    )
                    electrode_metrics[electrode]["out_strength"].append(
                        metrics["out_strength"]
                    )
                    electrode_metrics[electrode]["causal_flow"].append(
                        metrics["causal_flow"]
                    )

        # Calculate averages
        averaged_nodal = {}
        for electrode, metrics in electrode_metrics.items():
            if metrics["in_strength"]:  # Only if we have data
                averaged_nodal[electrode] = {
                    "in_strength": np.mean(metrics["in_strength"]),
                    "out_strength": np.mean(metrics["out_strength"]),
                    "causal_flow": np.mean(metrics["causal_flow"]),
                    "category": (
                        "sender"
                        if np.mean(metrics["causal_flow"]) > 0.001
                        else (
                            "receiver"
                            if np.mean(metrics["causal_flow"]) < -0.001
                            else "neutral"
                        )
                    ),
                }

        condition_averages[condition] = averaged_nodal

    # Calculate global scales across all conditions
    all_in_strength = []
    all_out_strength = []
    all_causal_flow = []

    for condition_nodal in condition_averages.values():
        for electrode, metrics in condition_nodal.items():
            all_in_strength.append(metrics["in_strength"])
            all_out_strength.append(metrics["out_strength"])
            all_causal_flow.append(metrics["causal_flow"])

    if all_in_strength:
        # Calculate global scales with padding
        in_min, in_max = min(all_in_strength), max(all_in_strength)
        out_min, out_max = min(all_out_strength), max(all_out_strength)
        flow_min, flow_max = min(all_causal_flow), max(all_causal_flow)

        # Add 5% padding
        in_range = in_max - in_min
        out_range = out_max - out_min
        flow_range = flow_max - flow_min

        padding_in = in_range * 0.05 if in_range > 0 else 0.0001
        padding_out = out_range * 0.05 if out_range > 0 else 0.0001
        padding_flow = flow_range * 0.05 if flow_range > 0 else 0.0001

        global_scales = {
            "in_strength": (in_min - padding_in, in_max + padding_in),
            "out_strength": (out_min - padding_out, out_max + padding_out),
            "causal_flow": (flow_min - padding_flow, flow_max + padding_flow),
        }

        # Generate condition-level visualizations
        by_condition_dir = os.path.join(output_dir, "by_condition")

        for condition, averaged_nodal in condition_averages.items():
            title = f"Average Nodal Metrics: {condition} (n={len(analyses_by_condition[condition])} participants)"
            title += f" - Global Scale"
            output_path = os.path.join(
                by_condition_dir, f"average_{condition}_nodal.png"
            )

            plot_nodal_metrics(averaged_nodal, title, output_path, scales=global_scales)

            print(f"  Generated: average_{condition}_nodal.png")

    print(f"  Condition-level nodal visualizations saved to: {by_condition_dir}")
