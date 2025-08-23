#!/usr/bin/env python3
"""
Cached Data Loader Service for Granger Causality Analysis

This service enhances the data loader with database caching to prevent
redundant file processing and speed up repeated operations.
"""

import os
import traceback
from typing import Dict, List, Tuple, Optional
from granger_analysis import GrangerCausalityAnalyzer
from .data_loader_service import extract_metadata_from_filename, find_input_files
from .database_service import DatabaseService


class CachedDataLoaderService:
    """Enhanced data loader with database caching capabilities"""

    def __init__(self, db_path: str = "granger_cache.db"):
        """
        Initialize the cached data loader service

        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_service = DatabaseService(db_path)

    def get_file_metadata_with_cache(self, file_path: str) -> Dict:
        """
        Get file metadata, using cache if available or extracting if not

        Args:
            file_path (str): Path to the file

        Returns:
            dict: File metadata
        """
        # First try to get from cache
        cached_metadata = self.db_service.get_file_metadata(file_path)

        if cached_metadata:
            print(f"  Using cached metadata for: {os.path.basename(file_path)}")
            return cached_metadata

        # Extract metadata and cache it
        filename = os.path.basename(file_path)
        metadata = extract_metadata_from_filename(filename)

        try:
            self.db_service.register_file(file_path, metadata)
            print(f"  Extracted and cached metadata for: {filename}")
        except Exception as e:
            print(f"  Warning: Could not cache metadata for {filename}: {e}")

        return metadata

    def load_single_file_with_cache(
        self,
        analyzer: GrangerCausalityAnalyzer,
        file_path: str,
        force_reload: bool = False,
    ) -> bool:
        """
        Load a single file with caching support

        Args:
            analyzer: GrangerCausalityAnalyzer instance
            file_path (str): Path to the file to load
            force_reload (bool): Force reload even if cached

        Returns:
            bool: True if loaded successfully
        """
        filename = os.path.basename(file_path)

        # Check if we have cached results and file hasn't changed
        if not force_reload and self.db_service.is_file_cached(file_path):
            print(f"  Loading cached analysis for: {filename}")

            try:
                # Get cached analysis
                cached_result = self.db_service.get_cached_analysis(
                    file_path, "granger_causality"
                )
                if cached_result:
                    # Get metadata
                    metadata = self.get_file_metadata_with_cache(file_path)

                    # Create analysis key
                    analysis_key = f"{metadata['participant_id']}_{metadata['condition']}_{metadata['timepoint']}"

                    # Add to analyzer
                    analyzer.analyses[analysis_key] = {
                        "metadata": metadata,
                        "connectivity_matrix": cached_result["connectivity_matrix"],
                        "global": cached_result["global_metrics"],
                        "electrode_list": cached_result["electrode_list"],
                    }

                    print(f"  ✓ Loaded from cache: {filename}")
                    return True
            except Exception as e:
                print(f"  Warning: Failed to load cached result for {filename}: {e}")
                # Fall through to normal loading

        # Load file normally and cache the result
        try:
            # Get metadata
            metadata = self.get_file_metadata_with_cache(file_path)

            # Load data with metadata
            analyzer.load_data_with_metadata(file_path, metadata)

            print(f"  ✓ Loaded and will cache: {filename}")
            return True

        except Exception as e:
            print(f"  ✗ Failed to load: {filename}: {str(e)}")
            traceback.print_exc()
            return False

    def cache_analysis_results(
        self, analyzer: GrangerCausalityAnalyzer, file_paths: List[str]
    ):
        """
        Cache analysis results for loaded files

        Args:
            analyzer: GrangerCausalityAnalyzer instance with completed analyses
            file_paths: List of file paths that were analyzed
        """
        print("\nCaching analysis results...")

        # Create a mapping from analysis keys to file paths
        analysis_to_file = {}
        for file_path in file_paths:
            metadata = self.get_file_metadata_with_cache(file_path)
            analysis_key = f"{metadata['participant_id']}_{metadata['condition']}_{metadata['timepoint']}"
            analysis_to_file[analysis_key] = file_path

        # Cache results for each analysis
        cached_count = 0
        for analysis_key, analysis in analyzer.analyses.items():
            if analysis_key in analysis_to_file:
                file_path = analysis_to_file[analysis_key]

                try:
                    # Check if already cached and up to date
                    if not self.db_service.is_file_cached(file_path):
                        self.db_service.cache_analysis_result(
                            file_path=file_path,
                            analysis_type="granger_causality",
                            connectivity_matrix=analysis["connectivity_matrix"],
                            global_metrics=analysis.get("global", {}),
                            analysis_params={},  # Could be extended with actual parameters
                        )
                        cached_count += 1
                except Exception as e:
                    print(f"  Warning: Failed to cache results for {file_path}: {e}")

        print(f"  Cached {cached_count} new analysis results")

    def load_and_analyze_files_with_cache(
        self, input_dir: str, force_reload: bool = False
    ) -> Tuple[GrangerCausalityAnalyzer, int, int]:
        """
        Load and analyze files with caching support

        Args:
            input_dir (str): Path to input directory
            force_reload (bool): Force reload all files even if cached

        Returns:
            tuple: (analyzer, successful_loads, failed_loads)
        """
        # Find all Excel files
        excel_files = find_input_files(input_dir)

        if not excel_files:
            print(f"No Excel files found in {input_dir}")
            return None, 0, 0

        print(f"Found {len(excel_files)} Excel files to process")
        if not force_reload:
            # Check how many are cached
            cached_count = sum(
                1 for f in excel_files if self.db_service.is_file_cached(f)
            )
            print(f"  {cached_count} files have cached results")
            print(f"  {len(excel_files) - cached_count} files need processing")

        # Initialize the analyzer
        analyzer = GrangerCausalityAnalyzer()

        # Load each file (with caching)
        successful_loads = 0
        failed_loads = 0

        for file_path in excel_files:
            if self.load_single_file_with_cache(analyzer, file_path, force_reload):
                successful_loads += 1
            else:
                failed_loads += 1

        print(f"\nLoading Summary:")
        print(f"  Successfully loaded: {successful_loads} files")
        print(f"  Failed to load: {failed_loads} files")

        if successful_loads == 0:
            print("No files were successfully loaded.")
            return analyzer, successful_loads, failed_loads

        # Check if we need to run analysis (only if we have uncached files)
        uncached_files = [
            f
            for f in excel_files
            if not self.db_service.is_file_cached(f) or force_reload
        ]

        if uncached_files or force_reload:
            print(f"\nRunning analysis on {len(uncached_files)} uncached files...")
            try:
                analyzer.analyze_all_data()
                print("✓ Analysis completed successfully")

                # Cache the new results
                self.cache_analysis_results(analyzer, uncached_files)

            except Exception as e:
                print(f"✗ Analysis failed: {str(e)}")
                traceback.print_exc()
                raise
        else:
            print("\nAll files loaded from cache - no analysis needed")

        return analyzer, successful_loads, failed_loads

    def get_cached_file_list(
        self, condition: str = None, participant_id: str = None
    ) -> List[Dict]:
        """
        Get list of cached files with optional filtering

        Args:
            condition (str, optional): Filter by condition
            participant_id (str, optional): Filter by participant ID

        Returns:
            list: List of cached file records
        """
        return self.db_service.get_all_files(
            condition=condition, participant_id=participant_id
        )

    def cleanup_cache(self):
        """Clean up orphaned cache records"""
        print("Cleaning up cache...")
        self.db_service.cleanup_orphaned_records()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.db_service.get_database_stats()

    def clear_file_cache(self, file_path: str):
        """
        Clear cache for a specific file (useful for testing or forced refresh)

        Args:
            file_path (str): Path to the file to clear from cache
        """
        # This would require adding a method to DatabaseService
        # For now, we can force reload by using force_reload=True
        pass


# Convenience functions
def get_cached_data_loader(
    db_path: str = "granger_cache.db",
) -> CachedDataLoaderService:
    """Get a cached data loader service instance"""
    return CachedDataLoaderService(db_path)


def load_files_with_cache(
    input_dir: str, db_path: str = "granger_cache.db", force_reload: bool = False
) -> Tuple[GrangerCausalityAnalyzer, int, int]:
    """
    Convenience function to load and analyze files with caching

    Args:
        input_dir (str): Input directory path
        db_path (str): Database path
        force_reload (bool): Force reload even if cached

    Returns:
        tuple: (analyzer, successful_loads, failed_loads)
    """
    service = CachedDataLoaderService(db_path)
    return service.load_and_analyze_files_with_cache(input_dir, force_reload)
