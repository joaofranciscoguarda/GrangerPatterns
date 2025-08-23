#!/usr/bin/env python3
"""
Batch Nodal Processor for Granger Causality Analysis

This script processes multiple Excel files from an input directory and generates
nodal visualizations with consistent scaling and condition-level analysis.
"""

import os
import sys
import asyncio
from services import (
    load_files_with_cache,  # Using cached version instead of load_and_analyze_files
    generate_individual_nodal_visualizations,
    generate_condition_level_nodal_visualizations,
    generate_nodal_analysis_report,
    create_nodal_output_directories,
    validate_input_directory,
    get_database_service,
)


async def process_nodal_analysis(input_dir="input", output_dir="output"):
    """Process files and generate nodal visualizations"""

    # Validate input directory
    if not validate_input_directory(input_dir):
        return False

    print("Granger Causality Nodal Analysis - Batch Processor")
    print("=" * 60)

    # Initialize database and show initial stats
    db_service = get_database_service()
    initial_stats = db_service.get_database_stats()
    print(f"\nCache Status:")
    print(f"  Cached files: {initial_stats['total_files']}")
    print(f"  Cached analyses: {initial_stats['cached_analyses']}")

    try:
        # Load and analyze files with caching
        print(f"\nLoading files from: {input_dir}")
        analyzer, successful_loads, failed_loads = load_files_with_cache(input_dir)

        if analyzer is None or successful_loads == 0:
            print("No files were successfully loaded. Exiting.")
            return False

        # Show updated cache stats
        final_stats = db_service.get_database_stats()
        if final_stats["cached_analyses"] > initial_stats["cached_analyses"]:
            new_cached = (
                final_stats["cached_analyses"] - initial_stats["cached_analyses"]
            )
            print(f"\n✓ Cached {new_cached} new analysis results for future use")

        # Create output directories
        print(f"\nCreating output directories in: {output_dir}")
        create_nodal_output_directories(output_dir)

        # Generate individual nodal visualizations
        print("\nGenerating individual nodal visualizations...")
        generate_individual_nodal_visualizations(analyzer, output_dir)

        # Generate condition-level nodal visualizations
        print("\nGenerating condition-level nodal visualizations...")
        generate_condition_level_nodal_visualizations(analyzer, output_dir)

        # Generate analysis report
        print("\nGenerating analysis report...")
        generate_nodal_analysis_report(
            analyzer, output_dir, successful_loads, failed_loads
        )

        print(f"\n✓ Nodal analysis completed successfully!")
        print(f"✓ Results saved to: {output_dir}")
        print(f"✓ Future runs will be faster due to caching")
        return True

    except Exception as e:
        print(f"\nError during nodal processing: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main function for standalone execution"""
    try:
        success = await process_nodal_analysis()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
