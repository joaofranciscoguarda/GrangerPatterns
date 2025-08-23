#!/usr/bin/env python3
"""
File System Service for Granger Causality Analysis

This service handles directory creation and file system operations.
"""

import os
import sys


def create_matrix_output_directories(output_dir):
    """
    Create necessary output directories for matrix processing

    Args:
        output_dir (str): Base output directory path
    """
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for matrix processing
    subdirs = [
        "matrices",  # For connectivity matrix visualizations
        "individual",  # For individual participant analyses
        "by_condition",  # Grouped by condition
        "by_timepoint",  # Grouped by timepoint
        "reports",  # For text reports/summaries
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print(f"Created matrix output directories in: {output_dir}")


def create_network_output_directories(output_dir):
    """
    Create necessary output directories for network processing

    Args:
        output_dir (str): Base output directory path
    """
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for network processing
    subdirs = [
        "networks",  # For network graph visualizations
        "individual",  # For individual participant analyses
        "by_condition",  # Grouped by condition
        "by_timepoint",  # Grouped by timepoint
        "reports",  # For text reports/summaries
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print(f"Created network output directories in: {output_dir}")


def create_nodal_output_directories(output_dir):
    """
    Create necessary output directories for nodal processing

    Args:
        output_dir (str): Base output directory path
    """
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for nodal processing
    subdirs = [
        "nodals",  # For nodal metric visualizations
        "individual",  # For individual participant analyses
        "by_condition",  # Grouped by condition
        "by_timepoint",  # Grouped by timepoint
        "reports",  # For text reports/summaries
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print(f"Created nodal output directories in: {output_dir}")


def create_pairwise_output_directories(output_dir):
    """
    Create necessary output directories for pairwise processing

    Args:
        output_dir (str): Base output directory path
    """
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for pairwise processing
    subdirs = [
        "pairwise",  # For pairwise connection visualizations
        "individual",  # For individual participant analyses
        "by_condition",  # Grouped by condition
        "by_timepoint",  # Grouped by timepoint
        "reports",  # For text reports/summaries
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print(f"Created pairwise output directories in: {output_dir}")


def create_global_output_directories(output_dir):
    """
    Create necessary output directories for global processing

    Args:
        output_dir (str): Base output directory path
    """
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for global processing
    subdirs = [
        "global",  # For global metric visualizations
        "individual",  # For individual participant analyses
        "by_condition",  # Grouped by condition
        "by_timepoint",  # Grouped by timepoint
        "reports",  # For text reports/summaries
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    print(f"Created global output directories in: {output_dir}")


def validate_input_directory(input_dir):
    """
    Validate that the input directory exists

    Args:
        input_dir (str): Path to input directory

    Returns:
        bool: True if directory exists, False otherwise
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print(
            f"Please create the '{input_dir}' directory and place your Excel files there."
        )
        return False

    return True
