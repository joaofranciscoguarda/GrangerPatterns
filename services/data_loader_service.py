#!/usr/bin/env python3
"""
Data Loader Service for Granger Causality Analysis

This service handles file discovery, metadata extraction, data loading, and analysis.
"""

import os
import re
import glob
import traceback
from granger_analysis import GrangerCausalityAnalyzer


def extract_metadata_from_filename(filename):
    """
    Extract metadata (participant ID, condition, timepoint, group) from filename

    Args:
        filename (str): The filename (without path)

    Returns:
        dict: Metadata dictionary with keys: participant_id, condition, timepoint, group
    """
    # Remove extension
    base_name = os.path.splitext(filename)[0]

    # Initialize metadata
    metadata = {
        "participant_id": "unknown",
        "condition": "unknown",
        "timepoint": "unknown",
        "group": "",
    }

    # Pattern 1: IDxCONyTIzGRw (full pattern with group)
    match = re.search(r"ID(\d+)CON(\d+)TI(\d+)GR(\d+)", base_name, re.IGNORECASE)
    if match:
        metadata["participant_id"] = match.group(1)
        metadata["condition"] = match.group(2)
        metadata["timepoint"] = match.group(3)
        metadata["group"] = match.group(4)
        return metadata

    # Pattern 2: IDxCONyTIz (no group)
    match = re.search(r"ID(\d+)CON(\d+)TI(\d+)", base_name, re.IGNORECASE)
    if match:
        metadata["participant_id"] = match.group(1)
        metadata["condition"] = match.group(2)
        metadata["timepoint"] = match.group(3)
        return metadata

    # Pattern 3: UTF format (UTF-xx_Ty_condition)
    match = re.search(r"UTF-(\w+)_T(\d+)_(\w+)", base_name, re.IGNORECASE)
    if match:
        metadata["participant_id"] = match.group(1)
        metadata["timepoint"] = match.group(2)
        metadata["condition"] = match.group(3)
        return metadata

    # Pattern 4: Simple underscore separated (participant_timepoint_condition)
    parts = base_name.split("_")
    if len(parts) >= 3:
        # Try to identify parts that look like participant ID, timepoint, condition
        for i, part in enumerate(parts):
            if part.startswith("UTF-") or part.startswith("ID"):
                metadata["participant_id"] = part.replace("UTF-", "").replace("ID", "")
            elif part.startswith("T") and part[1:].isdigit():
                metadata["timepoint"] = part
            elif part.startswith("CON") and part[3:].isdigit():
                metadata["condition"] = part[3:]
            elif i == 0 and not metadata["participant_id"] != "unknown":
                metadata["participant_id"] = part
            elif i == 1 and metadata["timepoint"] == "unknown":
                metadata["timepoint"] = part
            elif i == 2 and metadata["condition"] == "unknown":
                metadata["condition"] = part

    # Pattern 5: Simple participant_condition format (like 101_Baseline.xlsx)
    if len(parts) == 2:
        # First part is participant ID, second part is condition
        if parts[0].isdigit():
            metadata["participant_id"] = parts[0]
            metadata["condition"] = parts[1]
            metadata["timepoint"] = "T1"  # Default timepoint since not specified
            return metadata

    return metadata


def find_input_files(input_dir):
    """
    Find all Excel files in the input directory

    Args:
        input_dir (str): Path to input directory

    Returns:
        list: List of Excel file paths
    """
    excel_extensions = ["*.xlsx", "*.xls", "*.XLSX", "*.XLS"]
    files = []

    for ext in excel_extensions:
        pattern = os.path.join(input_dir, ext)
        files.extend(glob.glob(pattern))

    return sorted(files)


def load_and_analyze_files(input_dir):
    """
    Load and analyze all Excel files in the input directory

    Args:
        input_dir (str): Path to input directory

    Returns:
        tuple: (analyzer, successful_loads, failed_loads)
    """
    # Find all Excel files
    excel_files = find_input_files(input_dir)

    if not excel_files:
        print(f"No Excel files found in {input_dir}")
        return None, 0, 0

    print(f"Found {len(excel_files)} Excel files to process")

    # Initialize the analyzer
    analyzer = GrangerCausalityAnalyzer()

    # Process each file
    successful_loads = 0
    failed_loads = 0

    for file_path in excel_files:
        filename = os.path.basename(file_path)
        print(f"\nProcessing: {filename}")

        try:
            # Extract metadata from filename
            metadata = extract_metadata_from_filename(filename)
            print(
                f"  Extracted metadata: Participant={metadata['participant_id']}, "
                f"Condition={metadata['condition']}, Timepoint={metadata['timepoint']}"
            )

            # Check if metadata extraction was successful
            if (
                metadata["participant_id"] == "unknown"
                or metadata["condition"] == "unknown"
                or metadata["timepoint"] == "unknown"
            ):
                print(f"  Warning: Could not extract complete metadata from filename")
                print(f"  Using filename-based fallback...")

            # Load the data with metadata
            analyzer.load_data_with_metadata(file_path, metadata)
            successful_loads += 1
            print(f"  ✓ Loaded successfully")

        except Exception as e:
            failed_loads += 1
            print(f"  ✗ Failed to load: {str(e)}")
            traceback.print_exc()

    print(f"\nLoading Summary:")
    print(f"  Successfully loaded: {successful_loads} files")
    print(f"  Failed to load: {failed_loads} files")

    if successful_loads == 0:
        print("No files were successfully loaded.")
        return analyzer, successful_loads, failed_loads

    # Run analysis on all loaded data
    print("\nRunning analysis on all loaded data...")
    try:
        analyzer.analyze_all_data()
        print("✓ Analysis completed successfully")
    except Exception as e:
        print(f"✗ Analysis failed: {str(e)}")
        traceback.print_exc()
        raise

    return analyzer, successful_loads, failed_loads


def group_analyses_by_participant(analyzer):
    """
    Group analyses by participant ID

    Args:
        analyzer: GrangerCausalityAnalyzer instance

    Returns:
        dict: Dictionary mapping participant_id to list of (analysis_key, analysis) tuples
    """
    participant_analyses = {}
    for analysis_key, analysis in analyzer.analyses.items():
        participant_id = analysis["metadata"]["participant_id"]
        if participant_id not in participant_analyses:
            participant_analyses[participant_id] = []
        participant_analyses[participant_id].append((analysis_key, analysis))

    return participant_analyses


def group_analyses_by_condition(analyzer):
    """
    Group analyses by condition

    Args:
        analyzer: GrangerCausalityAnalyzer instance

    Returns:
        dict: Dictionary mapping condition to list of (analysis_key, analysis) tuples
    """
    condition_analyses = {}
    for analysis_key, analysis in analyzer.analyses.items():
        condition = analysis["metadata"]["condition"]
        if condition not in condition_analyses:
            condition_analyses[condition] = []
        condition_analyses[condition].append((analysis_key, analysis))

    return condition_analyses
