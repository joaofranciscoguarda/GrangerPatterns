#!/usr/bin/env python3
"""
Matrix Visualization Service for Granger Causality Analysis

This service handles matrix-specific visualization generation with consistent scaling.
"""

import os
import numpy as np
import pandas as pd
import traceback
from visualize_matrix import plot_connectivity_matrix
from .data_loader_service import (
    group_analyses_by_participant,
    group_analyses_by_condition,
)


def generate_individual_matrix_visualizations(analyzer, output_dir):
    """
    Generate individual matrix visualizations with consistent scaling per participant

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path

    Returns:
        int: Number of visualizations generated
    """
    print(f"\nGenerating matrix visualizations...")
    matrices_dir = os.path.join(output_dir, "matrices")
    individual_dir = os.path.join(output_dir, "individual")

    visualization_count = 0

    # Group analyses by participant to ensure consistent scaling
    participant_analyses = group_analyses_by_participant(analyzer)

    # Process each participant's data with consistent scaling
    for participant_id, analyses in participant_analyses.items():
        print(f"\n  Processing participant {participant_id}...")

        # Calculate min/max values across all conditions for this participant
        all_matrices = []
        for analysis_key, analysis in analyses:
            matrix = analysis["connectivity_matrix"]
            # Exclude diagonal values (they should be 0 or very close to 0)
            mask = ~np.eye(matrix.shape[0], dtype=bool)
            all_matrices.extend(matrix.values[mask].flatten())

        # Calculate global min/max for this participant
        global_min = np.min(all_matrices)
        global_max = np.max(all_matrices)

        print(f"    Scale range: {global_min:.6f} to {global_max:.6f}")

        # Generate visualizations for each condition with consistent scaling
        for analysis_key, analysis in analyses:
            try:
                # Get metadata
                condition = analysis["metadata"]["condition"]
                timepoint = analysis["metadata"]["timepoint"]

                # Create descriptive filename
                base_filename = f"{participant_id}_{timepoint}_{condition}"
                title = f"Granger Causality Matrix: {participant_id} {timepoint} {condition}"

                # Generate individual matrix visualization with consistent scaling
                matrix_path = os.path.join(
                    individual_dir, f"{base_filename}_matrix.png"
                )
                plot_connectivity_matrix(
                    analysis["connectivity_matrix"],
                    title,
                    matrix_path,
                    vmin=global_min,
                    vmax=global_max,
                )

                # Also save a copy in the matrices directory with a simpler name
                simple_matrix_path = os.path.join(matrices_dir, f"{base_filename}.png")
                plot_connectivity_matrix(
                    analysis["connectivity_matrix"],
                    title,
                    simple_matrix_path,
                    vmin=global_min,
                    vmax=global_max,
                )

                visualization_count += 1
                print(f"    ✓ Generated matrix for: {base_filename}")

            except Exception as e:
                print(f"    ✗ Failed to generate matrix for {analysis_key}: {str(e)}")
                traceback.print_exc()

    return visualization_count


def generate_condition_level_matrix_visualizations(analyzer, output_dir):
    """
    Generate condition-level matrix visualizations by averaging matrices across all participants

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path
    """
    print(f"\nGenerating condition-level matrix visualizations...")
    by_condition_dir = os.path.join(output_dir, "by_condition")

    try:
        # Group analyses by condition
        condition_analyses = group_analyses_by_condition(analyzer)

        print(
            f"  Found {len(condition_analyses)} conditions: {list(condition_analyses.keys())}"
        )

        # First pass: Calculate averaged matrices for all conditions
        condition_matrices = {}
        all_condition_values = []  # To calculate global scale

        for condition, analyses in condition_analyses.items():
            print(f"\n  Processing condition: {condition}")
            print(f"    Combining {len(analyses)} participants...")

            # Get all matrices for this condition
            matrices = []
            electrode_sets = []

            for analysis_key, analysis in analyses:
                matrix = analysis["connectivity_matrix"]
                matrices.append(matrix)
                electrode_sets.append(set(matrix.index))

            # Find common electrodes across all participants
            common_electrodes = electrode_sets[0]
            for electrode_set in electrode_sets[1:]:
                common_electrodes = common_electrodes.intersection(electrode_set)

            common_electrodes = sorted(list(common_electrodes))
            print(
                f"    Common electrodes ({len(common_electrodes)}): {', '.join(common_electrodes[:5])}{'...' if len(common_electrodes) > 5 else ''}"
            )

            if len(common_electrodes) == 0:
                print(f"    ✗ No common electrodes found for condition {condition}")
                continue

            # Create averaged matrix
            averaged_values = np.zeros((len(common_electrodes), len(common_electrodes)))

            for matrix in matrices:
                # Extract only common electrodes and add to average
                common_matrix = matrix.loc[common_electrodes, common_electrodes]
                averaged_values += common_matrix.values

            # Divide by number of participants to get average
            averaged_values /= len(matrices)

            # Create averaged DataFrame
            averaged_matrix = pd.DataFrame(
                averaged_values, index=common_electrodes, columns=common_electrodes
            )

            # Store the averaged matrix for this condition
            condition_matrices[condition] = averaged_matrix

            # Add values to global scale calculation (excluding diagonal)
            mask = ~np.eye(len(common_electrodes), dtype=bool)
            all_condition_values.extend(averaged_values[mask].flatten())

            print(f"    ✓ Averaged matrix calculated for {condition}")

        # Calculate global scale across all conditions
        if all_condition_values:
            global_min = np.min(all_condition_values)
            global_max = np.max(all_condition_values)
            print(
                f"\n  Global scale for all conditions: {global_min:.6f} to {global_max:.6f}"
            )
        else:
            print(f"\n  ✗ No data available for global scale calculation")
            return

        # Second pass: Generate visualizations with consistent global scale
        for condition, averaged_matrix in condition_matrices.items():
            print(f"\n  Generating visualization for condition: {condition}")

            # Generate visualization with global scale
            title = f"Average Granger Causality Matrix: {condition} Condition"
            subtitle = f"(n={len(condition_analyses[condition])} participants)"
            full_title = f"{title}\n{subtitle}"

            output_path = os.path.join(by_condition_dir, f"average_{condition}.png")
            plot_connectivity_matrix(
                averaged_matrix,
                full_title,
                output_path,
                vmin=global_min,
                vmax=global_max,
            )

            print(f"    ✓ Generated average matrix: average_{condition}.png")

            # Also save the averaged matrix data as CSV for further analysis
            csv_path = os.path.join(by_condition_dir, f"average_{condition}_matrix.csv")
            averaged_matrix.to_csv(csv_path)
            print(f"    ✓ Saved matrix data: average_{condition}_matrix.csv")

        print(f"\n  ✓ Condition-level visualizations completed with consistent scaling")

    except Exception as e:
        print(f"  ✗ Failed to generate condition-level visualizations: {str(e)}")
        traceback.print_exc()
