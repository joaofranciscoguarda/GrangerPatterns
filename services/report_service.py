#!/usr/bin/env python3
"""
Report Service for Granger Causality Analysis

This service handles the generation of analysis summary reports.
"""

import os
import numpy as np
from .network_visualization_service import create_network_graph_from_matrix


def generate_matrix_analysis_report(
    analyzer, output_dir, successful_loads=None, failed_loads=None
):
    """
    Generate a summary report for matrix analysis

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path
        successful_loads (int, optional): Number of successfully loaded files
        failed_loads (int, optional): Number of failed file loads
    """
    report_path = os.path.join(output_dir, "reports", "analysis_summary.txt")

    try:
        with open(report_path, "w") as f:
            f.write("Granger Causality Analysis Summary\n")
            f.write("=" * 40 + "\n\n")

            # Loading statistics
            if successful_loads is not None or failed_loads is not None:
                f.write("File Loading Statistics:\n")
                f.write("-" * 25 + "\n")
                if successful_loads is not None:
                    f.write(f"Successfully loaded files: {successful_loads}\n")
                if failed_loads is not None:
                    f.write(f"Failed to load files: {failed_loads}\n")
                f.write("\n")

            # General statistics
            f.write(f"Total analyses performed: {len(analyzer.analyses)}\n")
            f.write(
                f"Unique participants: {len(set(a['metadata']['participant_id'] for a in analyzer.analyses.values()))}\n"
            )
            f.write(
                f"Unique conditions: {len(set(a['metadata']['condition'] for a in analyzer.analyses.values()))}\n"
            )
            f.write(
                f"Unique timepoints: {len(set(a['metadata']['timepoint'] for a in analyzer.analyses.values()))}\n\n"
            )

            # List all analyses
            f.write("Individual Analyses:\n")
            f.write("-" * 20 + "\n")

            for analysis_key, analysis in analyzer.analyses.items():
                metadata = analysis["metadata"]
                f.write(f"Analysis: {analysis_key}\n")
                f.write(f"  Participant: {metadata['participant_id']}\n")
                f.write(f"  Condition: {metadata['condition']}\n")
                f.write(f"  Timepoint: {metadata['timepoint']}\n")

                # Add some basic metrics if available
                if "global" in analysis:
                    global_metrics = analysis["global"]
                    f.write(
                        f"  Global GC Strength: {global_metrics.get('global_gc_strength', 'N/A'):.6f}\n"
                    )
                    f.write(
                        f"  Mean GC Strength: {global_metrics.get('mean_gc_strength', 'N/A'):.6f}\n"
                    )

                # Matrix dimensions
                matrix = analysis["connectivity_matrix"]
                f.write(f"  Matrix size: {matrix.shape[0]} x {matrix.shape[1]}\n")
                f.write(
                    f"  Electrodes: {', '.join(matrix.index[:5])}{'...' if len(matrix.index) > 5 else ''}\n"
                )
                f.write("\n")

        print(f"  ✓ Generated summary report: {report_path}")

    except Exception as e:
        print(f"  ✗ Failed to generate summary report: {str(e)}")


def generate_nodal_analysis_report(
    analyzer, output_dir, successful_loads=None, failed_loads=None
):
    """Generate a comprehensive nodal analysis report

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
        successful_loads: Number of successfully loaded files (optional)
        failed_loads: Number of failed file loads (optional)

    Returns:
        str: Path to the generated report file
    """
    from .data_loader_service import (
        group_analyses_by_condition,
        group_analyses_by_participant,
    )
    from datetime import datetime
    import numpy as np

    report_path = os.path.join(output_dir, "reports", "nodal_analysis_summary.txt")

    try:
        with open(report_path, "w") as f:
            f.write("GRANGER CAUSALITY NODAL ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")

            # Basic statistics
            f.write("ANALYSIS OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total analyses: {len(analyzer.analyses)}\n")
            if successful_loads is not None:
                f.write(f"Successfully loaded files: {successful_loads}\n")
            if failed_loads is not None:
                f.write(f"Failed to load files: {failed_loads}\n")

            # Participant and condition breakdown
            analyses_by_participant = group_analyses_by_participant(analyzer)
            analyses_by_condition = group_analyses_by_condition(analyzer)

            f.write(f"Unique participants: {len(analyses_by_participant)}\n")
            f.write(f"Unique conditions: {len(analyses_by_condition)}\n\n")

            # Participant summary
            f.write("PARTICIPANT SUMMARY\n")
            f.write("-" * 20 + "\n")
            for participant_id, participant_analyses in analyses_by_participant.items():
                f.write(
                    f"Participant {participant_id}: {len(participant_analyses)} analyses\n"
                )
                conditions = set(
                    analysis["metadata"]["condition"]
                    for analysis_key, analysis in participant_analyses
                )
                f.write(f"  Conditions: {', '.join(sorted(conditions))}\n")
            f.write("\n")

            # Condition summary
            f.write("CONDITION SUMMARY\n")
            f.write("-" * 20 + "\n")
            for condition, condition_analyses in analyses_by_condition.items():
                f.write(f"Condition {condition}: {len(condition_analyses)} analyses\n")
                participants = set(
                    analysis["metadata"]["participant_id"]
                    for analysis_key, analysis in condition_analyses
                )
                f.write(f"  Participants: {', '.join(sorted(participants))}\n")
            f.write("\n")

            # Nodal metrics summary
            f.write("NODAL METRICS SUMMARY\n")
            f.write("-" * 25 + "\n")

            # Get electrode information from first analysis
            first_analysis = next(iter(analyzer.analyses.values()))
            electrodes = list(first_analysis["nodal"].keys())
            f.write(f"Number of electrodes: {len(electrodes)}\n")
            f.write(f"Electrodes: {', '.join(electrodes)}\n\n")

            # Overall statistics
            all_in_strength = []
            all_out_strength = []
            all_causal_flow = []

            for analysis in analyzer.analyses.values():
                for electrode, metrics in analysis["nodal"].items():
                    all_in_strength.append(metrics["in_strength"])
                    all_out_strength.append(metrics["out_strength"])
                    all_causal_flow.append(metrics["causal_flow"])

            f.write("OVERALL NODAL STATISTICS\n")
            f.write("-" * 25 + "\n")
            f.write(
                f"In-Strength - Mean: {np.mean(all_in_strength):.6f}, Std: {np.std(all_in_strength):.6f}\n"
            )
            f.write(
                f"            - Range: {min(all_in_strength):.6f} to {max(all_in_strength):.6f}\n"
            )
            f.write(
                f"Out-Strength - Mean: {np.mean(all_out_strength):.6f}, Std: {np.std(all_out_strength):.6f}\n"
            )
            f.write(
                f"             - Range: {min(all_out_strength):.6f} to {max(all_out_strength):.6f}\n"
            )
            f.write(
                f"Causal Flow - Mean: {np.mean(all_causal_flow):.6f}, Std: {np.std(all_causal_flow):.6f}\n"
            )
            f.write(
                f"            - Range: {min(all_causal_flow):.6f} to {max(all_causal_flow):.6f}\n\n"
            )

            # Condition-level statistics
            f.write("CONDITION-LEVEL STATISTICS\n")
            f.write("-" * 30 + "\n")

            for condition, condition_analyses in analyses_by_condition.items():
                f.write(f"\nCondition: {condition}\n")
                f.write("-" * (len(condition) + 11) + "\n")

                # Collect condition-specific metrics
                condition_in_strength = []
                condition_out_strength = []
                condition_causal_flow = []

                for analysis_key, analysis in condition_analyses:
                    for electrode, metrics in analysis["nodal"].items():
                        condition_in_strength.append(metrics["in_strength"])
                        condition_out_strength.append(metrics["out_strength"])
                        condition_causal_flow.append(metrics["causal_flow"])

                f.write(
                    f"In-Strength - Mean: {np.mean(condition_in_strength):.6f}, Std: {np.std(condition_in_strength):.6f}\n"
                )
                f.write(
                    f"Out-Strength - Mean: {np.mean(condition_out_strength):.6f}, Std: {np.std(condition_out_strength):.6f}\n"
                )
                f.write(
                    f"Causal Flow - Mean: {np.mean(condition_causal_flow):.6f}, Std: {np.std(condition_causal_flow):.6f}\n"
                )

            # Top sender/receiver electrodes
            f.write("\nTOP ELECTRODES BY CAUSAL FLOW\n")
            f.write("-" * 35 + "\n")

            # Calculate average causal flow per electrode across all analyses
            electrode_causal_flows = {electrode: [] for electrode in electrodes}

            for analysis in analyzer.analyses.values():
                for electrode, metrics in analysis["nodal"].items():
                    electrode_causal_flows[electrode].append(metrics["causal_flow"])

            # Calculate averages and sort
            electrode_averages = {
                electrode: np.mean(flows)
                for electrode, flows in electrode_causal_flows.items()
            }
            sorted_electrodes = sorted(
                electrode_averages.items(), key=lambda x: x[1], reverse=True
            )

            f.write("Top Senders (positive causal flow):\n")
            for electrode, avg_flow in sorted_electrodes[:5]:
                if avg_flow > 0:
                    f.write(f"  {electrode}: {avg_flow:.6f}\n")

            f.write("\nTop Receivers (negative causal flow):\n")
            for electrode, avg_flow in reversed(sorted_electrodes[-5:]):
                if avg_flow < 0:
                    f.write(f"  {electrode}: {avg_flow:.6f}\n")

            f.write(
                f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

        print(f"  ✓ Generated nodal summary report: {report_path}")
        return report_path

    except Exception as e:
        print(f"  ✗ Failed to generate nodal summary report: {str(e)}")
        return None


def generate_network_analysis_report(
    analyzer, output_dir, successful_loads=None, failed_loads=None
):
    """
    Generate a summary report for network analysis

    Args:
        analyzer: GrangerCausalityAnalyzer instance
        output_dir (str): Output directory path
        successful_loads (int, optional): Number of successfully loaded files
        failed_loads (int, optional): Number of failed file loads
    """
    report_path = os.path.join(output_dir, "reports", "network_analysis_summary.txt")

    try:
        with open(report_path, "w") as f:
            f.write("Granger Causality Network Analysis Summary\n")
            f.write("=" * 45 + "\n\n")

            # Loading statistics
            if successful_loads is not None or failed_loads is not None:
                f.write("File Loading Statistics:\n")
                f.write("-" * 25 + "\n")
                if successful_loads is not None:
                    f.write(f"Successfully loaded files: {successful_loads}\n")
                if failed_loads is not None:
                    f.write(f"Failed to load files: {failed_loads}\n")
                f.write("\n")

            # General statistics
            f.write(f"Total analyses performed: {len(analyzer.analyses)}\n")
            f.write(
                f"Unique participants: {len(set(a['metadata']['participant_id'] for a in analyzer.analyses.values()))}\n"
            )
            f.write(
                f"Unique conditions: {len(set(a['metadata']['condition'] for a in analyzer.analyses.values()))}\n"
            )
            f.write(
                f"Unique timepoints: {len(set(a['metadata']['timepoint'] for a in analyzer.analyses.values()))}\n\n"
            )

            # Network statistics for each analysis
            f.write("Network Statistics:\n")
            f.write("-" * 20 + "\n")

            for analysis_key, analysis in analyzer.analyses.items():
                metadata = analysis["metadata"]
                f.write(f"Analysis: {analysis_key}\n")
                f.write(f"  Participant: {metadata['participant_id']}\n")
                f.write(f"  Condition: {metadata['condition']}\n")
                f.write(f"  Timepoint: {metadata['timepoint']}\n")

                # Create network graph and get statistics
                G = create_network_graph_from_matrix(analysis["connectivity_matrix"])
                f.write(f"  Nodes: {G.number_of_nodes()}\n")
                f.write(f"  Edges: {G.number_of_edges()}\n")

                if G.number_of_edges() > 0:
                    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
                    f.write(f"  Average edge weight: {np.mean(edge_weights):.6f}\n")
                    f.write(f"  Max edge weight: {np.max(edge_weights):.6f}\n")
                    f.write(f"  Min edge weight: {np.min(edge_weights):.6f}\n")
                else:
                    f.write(f"  No edges above threshold\n")

                f.write("\n")

        print(f"  ✓ Generated network summary report: {report_path}")

    except Exception as e:
        print(f"  ✗ Failed to generate summary report: {str(e)}")


def generate_pairwise_analysis_report(
    analyzer, output_dir, successful_loads=None, failed_loads=None
):
    """Generate a comprehensive pairwise analysis report

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
        successful_loads: Number of successfully loaded files (optional)
        failed_loads: Number of failed file loads (optional)

    Returns:
        str: Path to the generated report file
    """
    from .data_loader_service import (
        group_analyses_by_condition,
        group_analyses_by_participant,
    )
    from datetime import datetime
    import numpy as np

    report_path = os.path.join(output_dir, "reports", "pairwise_analysis_summary.txt")

    try:
        with open(report_path, "w") as f:
            f.write("GRANGER CAUSALITY PAIRWISE ANALYSIS REPORT\n")
            f.write("=" * 52 + "\n\n")

            # Basic statistics
            f.write("ANALYSIS OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total analyses: {len(analyzer.analyses)}\n")
            if successful_loads is not None:
                f.write(f"Successfully loaded files: {successful_loads}\n")
            if failed_loads is not None:
                f.write(f"Failed to load files: {failed_loads}\n")

            # Participant and condition breakdown
            analyses_by_participant = group_analyses_by_participant(analyzer)
            analyses_by_condition = group_analyses_by_condition(analyzer)

            f.write(f"Unique participants: {len(analyses_by_participant)}\n")
            f.write(f"Unique conditions: {len(analyses_by_condition)}\n\n")

            # Participant summary
            f.write("PARTICIPANT SUMMARY\n")
            f.write("-" * 20 + "\n")
            for participant_id, participant_analyses in analyses_by_participant.items():
                f.write(
                    f"Participant {participant_id}: {len(participant_analyses)} analyses\n"
                )
                conditions = set(
                    analysis["metadata"]["condition"]
                    for analysis_key, analysis in participant_analyses
                )
                f.write(f"  Conditions: {', '.join(sorted(conditions))}\n")
            f.write("\n")

            # Condition summary
            f.write("CONDITION SUMMARY\n")
            f.write("-" * 20 + "\n")
            for condition, condition_analyses in analyses_by_condition.items():
                f.write(f"Condition {condition}: {len(condition_analyses)} analyses\n")
                participants = set(
                    analysis["metadata"]["participant_id"]
                    for analysis_key, analysis in condition_analyses
                )
                f.write(f"  Participants: {', '.join(sorted(participants))}\n")
            f.write("\n")

            # Pairwise connections summary
            f.write("PAIRWISE CONNECTIONS SUMMARY\n")
            f.write("-" * 32 + "\n")

            # Get connection pair information from first analysis
            first_analysis = next(iter(analyzer.analyses.values()))
            if (
                "pairwise" in first_analysis
                and "directional_pairs" in first_analysis["pairwise"]
            ):
                pairs = list(first_analysis["pairwise"]["directional_pairs"].keys())
                f.write(f"Number of directional pairs: {len(pairs)}\n")
                f.write(f"Connection pairs: {', '.join(pairs[:10])}")  # Show first 10
                if len(pairs) > 10:
                    f.write(f" ... and {len(pairs)-10} more")
                f.write("\n\n")

                # Overall statistics
                all_gc_values = []

                for analysis in analyzer.analyses.values():
                    if (
                        "pairwise" in analysis
                        and "directional_pairs" in analysis["pairwise"]
                    ):
                        all_gc_values.extend(
                            analysis["pairwise"]["directional_pairs"].values()
                        )

                if all_gc_values:
                    f.write("OVERALL PAIRWISE STATISTICS\n")
                    f.write("-" * 32 + "\n")
                    f.write(
                        f"GC Values - Mean: {np.mean(all_gc_values):.6f}, Std: {np.std(all_gc_values):.6f}\n"
                    )
                    f.write(
                        f"          - Range: {min(all_gc_values):.6f} to {max(all_gc_values):.6f}\n\n"
                    )

                    # Condition-level statistics
                    f.write("CONDITION-LEVEL STATISTICS\n")
                    f.write("-" * 30 + "\n")

                    for condition, condition_analyses in analyses_by_condition.items():
                        f.write(f"\nCondition: {condition}\n")
                        f.write("-" * (len(condition) + 11) + "\n")

                        # Collect condition-specific values
                        condition_gc_values = []

                        for analysis_key, analysis in condition_analyses:
                            if (
                                "pairwise" in analysis
                                and "directional_pairs" in analysis["pairwise"]
                            ):
                                condition_gc_values.extend(
                                    analysis["pairwise"]["directional_pairs"].values()
                                )

                        if condition_gc_values:
                            f.write(
                                f"GC Values - Mean: {np.mean(condition_gc_values):.6f}, Std: {np.std(condition_gc_values):.6f}\n"
                            )
                            f.write(
                                f"          - Range: {min(condition_gc_values):.6f} to {max(condition_gc_values):.6f}\n"
                            )

                    # Top connections
                    f.write("\nTOP CONNECTIONS BY AVERAGE GC VALUE\n")
                    f.write("-" * 40 + "\n")

                    # Calculate average GC value per pair across all analyses
                    pair_gc_values = {pair: [] for pair in pairs}

                    for analysis in analyzer.analyses.values():
                        if (
                            "pairwise" in analysis
                            and "directional_pairs" in analysis["pairwise"]
                        ):
                            for pair, value in analysis["pairwise"][
                                "directional_pairs"
                            ].items():
                                if pair in pair_gc_values:
                                    pair_gc_values[pair].append(value)

                    # Calculate averages and sort
                    pair_averages = {
                        pair: np.mean(values)
                        for pair, values in pair_gc_values.items()
                        if values
                    }
                    sorted_pairs = sorted(
                        pair_averages.items(), key=lambda x: x[1], reverse=True
                    )

                    f.write("Strongest connections (top 10):\n")
                    for pair, avg_gc in sorted_pairs[:10]:
                        f.write(f"  {pair}: {avg_gc:.6f}\n")

                    f.write("\nWeakest connections (bottom 5):\n")
                    for pair, avg_gc in sorted_pairs[-5:]:
                        f.write(f"  {pair}: {avg_gc:.6f}\n")

            f.write(
                f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

        print(f"  ✓ Generated pairwise summary report: {report_path}")
        return report_path

    except Exception as e:
        print(f"  ✗ Failed to generate pairwise summary report: {str(e)}")
        return None


def generate_global_analysis_report(
    analyzer, output_dir, successful_loads=None, failed_loads=None
):
    """Generate a comprehensive global metrics analysis report

    Args:
        analyzer: GrangerCausalityAnalyzer instance with loaded analyses
        output_dir: Base output directory
        successful_loads: Number of successfully loaded files (optional)
        failed_loads: Number of failed file loads (optional)

    Returns:
        str: Path to the generated report file
    """
    from .data_loader_service import (
        group_analyses_by_condition,
        group_analyses_by_participant,
    )
    from datetime import datetime
    import numpy as np

    report_path = os.path.join(output_dir, "reports", "global_analysis_summary.txt")

    try:
        with open(report_path, "w") as f:
            f.write("GRANGER CAUSALITY GLOBAL METRICS ANALYSIS REPORT\n")
            f.write("=" * 55 + "\n\n")

            # Basic statistics
            f.write("ANALYSIS OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total analyses: {len(analyzer.analyses)}\n")
            if successful_loads is not None:
                f.write(f"Successfully loaded files: {successful_loads}\n")
            if failed_loads is not None:
                f.write(f"Failed to load files: {failed_loads}\n")

            # Participant and condition breakdown
            analyses_by_participant = group_analyses_by_participant(analyzer)
            analyses_by_condition = group_analyses_by_condition(analyzer)

            f.write(f"Unique participants: {len(analyses_by_participant)}\n")
            f.write(f"Unique conditions: {len(analyses_by_condition)}\n\n")

            # Participant summary
            f.write("PARTICIPANT SUMMARY\n")
            f.write("-" * 20 + "\n")
            for participant_id, participant_analyses in analyses_by_participant.items():
                f.write(
                    f"Participant {participant_id}: {len(participant_analyses)} analyses\n"
                )
                conditions = set(
                    analysis["metadata"]["condition"]
                    for analysis_key, analysis in participant_analyses
                )
                f.write(f"  Conditions: {', '.join(sorted(conditions))}\n")
            f.write("\n")

            # Condition summary
            f.write("CONDITION SUMMARY\n")
            f.write("-" * 20 + "\n")
            for condition, condition_analyses in analyses_by_condition.items():
                f.write(f"Condition {condition}: {len(condition_analyses)} analyses\n")
                participants = set(
                    analysis["metadata"]["participant_id"]
                    for analysis_key, analysis in condition_analyses
                )
                f.write(f"  Participants: {', '.join(sorted(participants))}\n")
            f.write("\n")

            # Global metrics summary
            f.write("GLOBAL METRICS SUMMARY\n")
            f.write("-" * 25 + "\n")

            # Get global metrics structure from first analysis
            first_analysis = next(iter(analyzer.analyses.values()))
            if "global" in first_analysis:
                global_data = first_analysis["global"]

                if isinstance(global_data, dict):
                    # Check if nested structure
                    any_dict_values = any(
                        isinstance(value, dict) for value in global_data.values()
                    )

                    if any_dict_values:
                        f.write(
                            "Nested structure detected (Category -> Metrics -> Values):\n"
                        )
                        for category, metrics in global_data.items():
                            if isinstance(metrics, dict):
                                f.write(
                                    f"  Category '{category}': {', '.join(metrics.keys())}\n"
                                )
                            else:
                                f.write(f"  Category '{category}': {metrics}\n")
                    else:
                        f.write("Flat structure detected (Metric -> Value):\n")
                        f.write(f"  Metrics: {', '.join(global_data.keys())}\n")
                else:
                    f.write(f"Single value structure: {type(global_data).__name__}\n")

                f.write("\n")

                # Overall statistics
                all_metric_values = []

                for analysis in analyzer.analyses.values():
                    if "global" in analysis:
                        global_metrics = analysis["global"]
                        if isinstance(global_metrics, dict):
                            # Flatten nested structure
                            for value in global_metrics.values():
                                if isinstance(value, dict):
                                    all_metric_values.extend(value.values())
                                else:
                                    all_metric_values.append(value)
                        else:
                            all_metric_values.append(global_metrics)

                if all_metric_values:
                    f.write("OVERALL GLOBAL METRICS STATISTICS\n")
                    f.write("-" * 38 + "\n")
                    f.write(
                        f"Metric Values - Mean: {np.mean(all_metric_values):.6f}, Std: {np.std(all_metric_values):.6f}\n"
                    )
                    f.write(
                        f"              - Range: {min(all_metric_values):.6f} to {max(all_metric_values):.6f}\n\n"
                    )

                    # Condition-level statistics
                    f.write("CONDITION-LEVEL STATISTICS\n")
                    f.write("-" * 30 + "\n")

                    for condition, condition_analyses in analyses_by_condition.items():
                        f.write(f"\nCondition: {condition}\n")
                        f.write("-" * (len(condition) + 11) + "\n")

                        # Collect condition-specific values
                        condition_metric_values = []

                        for analysis_key, analysis in condition_analyses:
                            if "global" in analysis:
                                global_metrics = analysis["global"]
                                if isinstance(global_metrics, dict):
                                    # Flatten nested structure
                                    for value in global_metrics.values():
                                        if isinstance(value, dict):
                                            condition_metric_values.extend(
                                                value.values()
                                            )
                                        else:
                                            condition_metric_values.append(value)
                                else:
                                    condition_metric_values.append(global_metrics)

                        if condition_metric_values:
                            f.write(
                                f"Metric Values - Mean: {np.mean(condition_metric_values):.6f}, Std: {np.std(condition_metric_values):.6f}\n"
                            )
                            f.write(
                                f"              - Range: {min(condition_metric_values):.6f} to {max(condition_metric_values):.6f}\n"
                            )

                    # Top metrics by average value
                    f.write("\nTOP METRICS BY AVERAGE VALUE\n")
                    f.write("-" * 35 + "\n")

                    # Get all unique metric names
                    all_metrics = set()
                    for analysis in analyzer.analyses.values():
                        if "global" in analysis:
                            global_metrics = analysis["global"]
                            if isinstance(global_metrics, dict):
                                for key, value in global_metrics.items():
                                    if isinstance(value, dict):
                                        all_metrics.update(value.keys())
                                    else:
                                        all_metrics.add(key)
                            else:
                                all_metrics.add("global_value")

                    # Calculate averages per metric
                    metric_averages = {}
                    for metric_name in all_metrics:
                        metric_values = []

                        for analysis in analyzer.analyses.values():
                            if "global" in analysis:
                                global_metrics = analysis["global"]
                                if isinstance(global_metrics, dict):
                                    for key, value in global_metrics.items():
                                        if (
                                            isinstance(value, dict)
                                            and metric_name in value
                                        ):
                                            metric_values.append(value[metric_name])
                                        elif key == metric_name:
                                            metric_values.append(value)
                                else:
                                    if metric_name == "global_value":
                                        metric_values.append(global_metrics)

                        if metric_values:
                            metric_averages[metric_name] = np.mean(metric_values)

                    # Sort and display
                    sorted_metrics = sorted(
                        metric_averages.items(), key=lambda x: x[1], reverse=True
                    )

                    f.write("Highest average metrics (top 10):\n")
                    for metric_name, avg_value in sorted_metrics[:10]:
                        f.write(f"  {metric_name}: {avg_value:.6f}\n")

                    f.write("\nLowest average metrics (bottom 5):\n")
                    for metric_name, avg_value in sorted_metrics[-5:]:
                        f.write(f"  {metric_name}: {avg_value:.6f}\n")

            f.write(
                f"\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

        print(f"  ✓ Generated global summary report: {report_path}")
        return report_path

    except Exception as e:
        print(f"  ✗ Failed to generate global summary report: {str(e)}")
        return None
