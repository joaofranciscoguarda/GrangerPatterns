#!/usr/bin/env python3
"""
Network Visualization Service for Granger Causality Analysis

This service handles network-specific visualization generation with consistent scaling.
"""

import os
import numpy as np
import pandas as pd
import traceback
import networkx as nx
from visualize_network import plot_network_graph
from .data_loader_service import (
    group_analyses_by_participant,
    group_analyses_by_condition,
)


def create_network_graph_from_matrix(matrix, threshold=0.0005):
    """
    Create a NetworkX graph from a connectivity matrix

    Args:
        matrix (pandas.DataFrame): Connectivity matrix
        threshold (float): Minimum edge weight to include in graph

    Returns:
        networkx.DiGraph: Directed graph representing connectivity
    """
    G = nx.DiGraph()

    # Add all nodes (electrodes)
    G.add_nodes_from(matrix.index)

    # Add edges with weights above threshold
    for source in matrix.index:
        for target in matrix.columns:
            if source != target:  # Skip diagonal (self-connections)
                weight = matrix.loc[source, target]
                if weight > threshold:
                    G.add_edge(source, target, weight=weight)

    return G


def generate_individual_network_visualizations(analyzer, output_dir):
    """
    Generate individual network visualizations with consistent scaling per participant

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path

    Returns:
        int: Number of visualizations generated
    """
    print(f"\nGenerating network visualizations...")
    networks_dir = os.path.join(output_dir, "networks")
    individual_dir = os.path.join(output_dir, "individual")

    visualization_count = 0

    # Group analyses by participant to ensure consistent scaling
    participant_analyses = group_analyses_by_participant(analyzer)

    # Process each participant's data with consistent scaling
    for participant_id, analyses in participant_analyses.items():
        print(f"\n  Processing participant {participant_id}...")

        # Calculate min/max edge weights across all conditions for this participant
        all_edge_weights = []
        for analysis_key, analysis in analyses:
            matrix = analysis["connectivity_matrix"]
            # Get all non-diagonal values as potential edge weights
            mask = ~np.eye(matrix.shape[0], dtype=bool)
            matrix_values = matrix.values[mask]
            # Only include values above threshold as actual edges
            edge_values = matrix_values[matrix_values > 0.0005]
            all_edge_weights.extend(edge_values)

        # Calculate global min/max for edge weights for this participant
        if all_edge_weights:
            global_min = np.min(all_edge_weights)
            global_max = np.max(all_edge_weights)
            print(f"    Edge weight range: {global_min:.6f} to {global_max:.6f}")
        else:
            global_min = 0
            global_max = 0.001
            print(
                f"    No edges above threshold, using default range: {global_min:.6f} to {global_max:.6f}"
            )

        # Generate network visualizations for each condition with consistent scaling
        for analysis_key, analysis in analyses:
            try:
                # Get metadata
                condition = analysis["metadata"]["condition"]
                timepoint = analysis["metadata"]["timepoint"]

                # Create descriptive filename
                base_filename = f"{participant_id}_{timepoint}_{condition}"
                title = f"Granger Causality Network: {participant_id} {timepoint} {condition}"

                # Create network graph from connectivity matrix
                G = create_network_graph_from_matrix(analysis["connectivity_matrix"])

                # Generate individual network visualization
                network_path = os.path.join(
                    individual_dir, f"{base_filename}_network.png"
                )
                plot_network_graph(
                    G, title, network_path, vmin=global_min, vmax=global_max
                )

                # Also save a copy in the networks directory with a simpler name
                simple_network_path = os.path.join(networks_dir, f"{base_filename}.png")
                plot_network_graph(
                    G, title, simple_network_path, vmin=global_min, vmax=global_max
                )

                visualization_count += 1
                print(f"    ✓ Generated network for: {base_filename}")

            except Exception as e:
                print(f"    ✗ Failed to generate network for {analysis_key}: {str(e)}")
                traceback.print_exc()

    return visualization_count


def generate_condition_level_network_visualizations(analyzer, output_dir):
    """
    Generate condition-level network visualizations by averaging matrices across all participants

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path
    """
    print(f"\nGenerating condition-level network visualizations...")
    by_condition_dir = os.path.join(output_dir, "by_condition")

    try:
        # Group analyses by condition
        condition_analyses = group_analyses_by_condition(analyzer)

        print(
            f"  Found {len(condition_analyses)} conditions: {list(condition_analyses.keys())}"
        )

        # First pass: Calculate averaged matrices for all conditions
        condition_matrices = {}
        all_condition_edge_weights = []  # To calculate global scale

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

            # Add edge weights to global scale calculation (excluding diagonal, above threshold)
            mask = ~np.eye(len(common_electrodes), dtype=bool)
            matrix_values = averaged_values[mask]
            edge_values = matrix_values[matrix_values > 0.0005]
            all_condition_edge_weights.extend(edge_values)

            print(f"    ✓ Averaged matrix calculated for {condition}")

        # Calculate global scale across all conditions for edge weights
        if all_condition_edge_weights:
            global_min = np.min(all_condition_edge_weights)
            global_max = np.max(all_condition_edge_weights)
            print(
                f"\n  Global edge weight scale for all conditions: {global_min:.6f} to {global_max:.6f}"
            )
        else:
            global_min = 0
            global_max = 0.001
            print(
                f"\n  No edges above threshold, using default range: {global_min:.6f} to {global_max:.6f}"
            )

        # Second pass: Generate network visualizations with consistent global scale
        for condition, averaged_matrix in condition_matrices.items():
            print(f"\n  Generating network visualization for condition: {condition}")

            # Generate network visualization
            title = f"Average Granger Causality Network: {condition} Condition"
            subtitle = f"(n={len(condition_analyses[condition])} participants)"
            full_title = f"{title}\n{subtitle}"

            # Create network graph from averaged connectivity matrix
            G_avg = create_network_graph_from_matrix(averaged_matrix)

            output_path = os.path.join(
                by_condition_dir, f"average_{condition}_network.png"
            )
            plot_network_graph(
                G_avg, full_title, output_path, vmin=global_min, vmax=global_max
            )

            print(f"    ✓ Generated average network: average_{condition}_network.png")

            # Also save the averaged matrix data as CSV for further analysis
            csv_path = os.path.join(
                by_condition_dir, f"average_{condition}_network_matrix.csv"
            )
            averaged_matrix.to_csv(csv_path)
            print(
                f"    ✓ Saved network matrix data: average_{condition}_network_matrix.csv"
            )

        print(f"\n  ✓ Condition-level network visualizations completed")

    except Exception as e:
        print(
            f"  ✗ Failed to generate condition-level network visualizations: {str(e)}"
        )
        traceback.print_exc()
