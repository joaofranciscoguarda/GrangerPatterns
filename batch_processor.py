#!/usr/bin/env python3
"""
Unified Batch Processor for Granger Causality Analysis

This script provides a unified interface to run multiple types of analysis:
- Matrix visualizations
- Network visualizations
- Nodal visualizations
- Pairwise visualizations
- Global metric visualizations

Usage:
    python batch_processor.py --all                    # Run all analyses
    python batch_processor.py --matrix --network       # Run specific analyses
    python batch_processor.py --help                   # Show help
"""

import os
import sys
import asyncio
import argparse
from typing import List, Dict, Any

# Import all the async processing functions
from batch_matrix_processor import process_matrix_analysis
from batch_network_processor import process_network_analysis
from batch_nodal_processor import process_nodal_analysis
from batch_pairwise_processor import process_pairwise_analysis
from batch_global_processor import process_global_analysis


# Analysis type definitions
ANALYSIS_TYPES = {
    "matrix": {
        "name": "Matrix Visualizations",
        "function": process_matrix_analysis,
        "description": "Connectivity matrix heatmaps with consistent scaling",
    },
    "network": {
        "name": "Network Visualizations",
        "function": process_network_analysis,
        "description": "Network graph visualizations with consistent scaling",
    },
    "nodal": {
        "name": "Nodal Visualizations",
        "function": process_nodal_analysis,
        "description": "Nodal metric bar charts with consistent scaling",
    },
    "pairwise": {
        "name": "Pairwise Visualizations",
        "function": process_pairwise_analysis,
        "description": "Pairwise connection strength plots with consistent scaling",
    },
    "global": {
        "name": "Global Metrics Visualizations",
        "function": process_global_analysis,
        "description": "Global metric bar charts with consistent scaling",
    },
}


async def run_analysis(
    analysis_type: str, input_dir: str, output_dir: str, semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """Run a single analysis type with semaphore control"""
    async with semaphore:
        print(f"\n{'='*80}")
        print(f"Starting {ANALYSIS_TYPES[analysis_type]['name']}")
        print(f"{'='*80}")

        try:
            start_time = asyncio.get_event_loop().time()
            success = await ANALYSIS_TYPES[analysis_type]["function"](
                input_dir, output_dir
            )
            end_time = asyncio.get_event_loop().time()

            return {
                "type": analysis_type,
                "success": success,
                "duration": end_time - start_time,
                "name": ANALYSIS_TYPES[analysis_type]["name"],
            }
        except Exception as e:
            print(f"❌ Error in {analysis_type} analysis: {str(e)}")
            return {
                "type": analysis_type,
                "success": False,
                "error": str(e),
                "name": ANALYSIS_TYPES[analysis_type]["name"],
            }


async def run_analyses(
    selected_types: List[str], input_dir: str, output_dir: str, max_concurrent: int = 2
) -> List[Dict[str, Any]]:
    """Run multiple analyses concurrently with controlled concurrency"""

    if not selected_types:
        print("No analysis types selected!")
        return []

    print(f"\n🚀 Starting {len(selected_types)} analysis types...")
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⚡ Max concurrent processes: {max_concurrent}")

    # Create semaphore to limit concurrent processes
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create tasks for all selected analyses
    tasks = [
        run_analysis(analysis_type, input_dir, output_dir, semaphore)
        for analysis_type in selected_types
    ]

    # Run all analyses concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Unexpected error: {result}")
            processed_results.append(
                {
                    "type": "unknown",
                    "success": False,
                    "error": str(result),
                    "name": "Unknown Analysis",
                }
            )
        else:
            processed_results.append(result)

    return processed_results


def print_results_summary(results: List[Dict[str, Any]]):
    """Print a summary of all analysis results"""
    print(f"\n{'='*80}")
    print("📊 ANALYSIS RESULTS SUMMARY")
    print(f"{'='*80}")

    successful = 0
    failed = 0

    for result in results:
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        duration = f"({result['duration']:.1f}s)" if "duration" in result else ""
        error_info = f" - Error: {result['error']}" if "error" in result else ""

        print(f"{status} {result['name']} {duration}{error_info}")

        if result["success"]:
            successful += 1
        else:
            failed += 1

    print(f"\n📈 SUMMARY:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📊 Total: {len(results)}")

    if failed == 0:
        print(f"\n🎉 All analyses completed successfully!")
    else:
        print(
            f"\n⚠️  {failed} analysis type(s) failed. Check the logs above for details."
        )


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Unified Batch Processor for Granger Causality Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_processor.py --all                    # Run all analyses
  python batch_processor.py --matrix --network       # Run matrix and network only
  python batch_processor.py --nodal --global-metrics         # Run nodal and global only
  python batch_processor.py --input custom_input     # Use custom input directory
  python batch_processor.py --output custom_output   # Use custom output directory
  python batch_processor.py --concurrent 3           # Allow 3 concurrent processes
        """,
    )

    # Analysis type arguments
    parser.add_argument("--all", action="store_true", help="Run all analysis types")
    parser.add_argument(
        "--matrix", action="store_true", help="Run matrix visualizations"
    )
    parser.add_argument(
        "--network", action="store_true", help="Run network visualizations"
    )
    parser.add_argument("--nodal", action="store_true", help="Run nodal visualizations")
    parser.add_argument(
        "--pairwise", action="store_true", help="Run pairwise visualizations"
    )
    parser.add_argument(
        "--global-metrics",
        action="store_true",
        help="Run global metrics visualizations",
    )

    # Directory arguments
    parser.add_argument(
        "--input",
        default="input",
        help="Input directory containing Excel files (default: input)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory for results (default: output)",
    )

    # Performance arguments
    parser.add_argument(
        "--concurrent",
        type=int,
        default=2,
        help="Maximum concurrent processes (default: 2)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Determine which analyses to run
    selected_types = []

    if args.all:
        selected_types = list(ANALYSIS_TYPES.keys())
    else:
        if args.matrix:
            selected_types.append("matrix")
        if args.network:
            selected_types.append("network")
        if args.nodal:
            selected_types.append("nodal")
        if args.pairwise:
            selected_types.append("pairwise")
        if args.global_metrics:
            selected_types.append("global")

    if not selected_types:
        print("❌ No analysis types selected!")
        print("Use --help to see available options")
        print("Use --all to run all analyses")
        sys.exit(1)

    # Validate directories
    if not os.path.exists(args.input):
        print(f"❌ Input directory '{args.input}' does not exist!")
        sys.exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Show what will be run
    print(f"🎯 Selected Analysis Types:")
    for analysis_type in selected_types:
        info = ANALYSIS_TYPES[analysis_type]
        print(f"  • {info['name']}: {info['description']}")

    # Run the analyses
    try:
        results = asyncio.run(
            run_analyses(selected_types, args.input, args.output, args.concurrent)
        )

        print_results_summary(results)

        # Exit with error code if any analysis failed
        if any(not result["success"] for result in results):
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
