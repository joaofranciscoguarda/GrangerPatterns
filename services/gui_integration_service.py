#!/usr/bin/env python3
"""
GUI Integration Service for Granger Causality Analysis

This service provides easy-to-use methods for GUI integration with the caching system,
allowing the GUI to quickly populate file lists, get metadata, and load cached analyses.
"""

import os
from typing import Dict, List, Optional, Tuple
from .cached_data_loader_service import CachedDataLoaderService
from .database_service import DatabaseService
from granger_analysis import GrangerCausalityAnalyzer


class GUIIntegrationService:
    """Service to bridge the GUI with the caching system"""

    def __init__(self, db_path: str = "granger_cache.db"):
        """
        Initialize the GUI integration service

        Args:
            db_path (str): Path to the SQLite database file
        """
        self.cached_loader = CachedDataLoaderService(db_path)
        self.db_service = DatabaseService(db_path)

    def get_available_files(self) -> List[Dict]:
        """
        Get all files that have been processed and cached

        Returns:
            list: List of file records with metadata
        """
        return self.db_service.get_all_files()

    def get_files_by_participant(self) -> Dict[str, List[Dict]]:
        """
        Get files organized by participant ID

        Returns:
            dict: Dictionary mapping participant_id to list of file records
        """
        files = self.get_available_files()
        participants = {}

        for file_record in files:
            pid = file_record["participant_id"]
            if pid and pid != "unknown":
                if pid not in participants:
                    participants[pid] = []
                participants[pid].append(file_record)

        # Sort participants by ID
        return dict(sorted(participants.items(), key=lambda x: x[0]))

    def get_files_by_condition(self) -> Dict[str, List[Dict]]:
        """
        Get files organized by condition

        Returns:
            dict: Dictionary mapping condition to list of file records
        """
        files = self.get_available_files()
        conditions = {}

        for file_record in files:
            condition = file_record["condition"]
            if condition and condition != "unknown":
                if condition not in conditions:
                    conditions[condition] = []
                conditions[condition].append(file_record)

        # Sort conditions alphabetically
        return dict(sorted(conditions.items()))

    def get_participant_conditions(self, participant_id: str) -> List[str]:
        """
        Get all conditions available for a specific participant

        Args:
            participant_id (str): The participant ID

        Returns:
            list: List of conditions for this participant
        """
        files = self.db_service.get_all_files(participant_id=participant_id)
        conditions = set()

        for file_record in files:
            condition = file_record["condition"]
            if condition and condition != "unknown":
                conditions.add(condition)

        return sorted(list(conditions))

    def get_file_summary_stats(self) -> Dict:
        """
        Get summary statistics about cached files

        Returns:
            dict: Summary statistics
        """
        stats = self.db_service.get_database_stats()
        files = self.get_available_files()

        # Additional GUI-friendly stats
        participants = set()
        conditions = set()
        timepoints = set()

        for file_record in files:
            if (
                file_record["participant_id"]
                and file_record["participant_id"] != "unknown"
            ):
                participants.add(file_record["participant_id"])
            if file_record["condition"] and file_record["condition"] != "unknown":
                conditions.add(file_record["condition"])
            if file_record["timepoint"] and file_record["timepoint"] != "unknown":
                timepoints.add(file_record["timepoint"])

        return {
            "total_files": stats["total_files"],
            "cached_analyses": stats["cached_analyses"],
            "unique_participants": len(participants),
            "unique_conditions": len(conditions),
            "unique_timepoints": len(timepoints),
            "participant_list": sorted(list(participants)),
            "condition_list": sorted(list(conditions)),
            "timepoint_list": sorted(list(timepoints)),
        }

    def load_selected_files(
        self, file_paths: List[str], force_reload: bool = False
    ) -> Tuple[GrangerCausalityAnalyzer, int, int]:
        """
        Load specific files selected by the GUI user

        Args:
            file_paths (list): List of file paths to load
            force_reload (bool): Force reload even if cached

        Returns:
            tuple: (analyzer, successful_loads, failed_loads)
        """
        # Create a temporary directory structure for the cached loader
        # Since it expects to find files in a directory
        analyzer = GrangerCausalityAnalyzer()

        successful_loads = 0
        failed_loads = 0

        for file_path in file_paths:
            if os.path.exists(file_path):
                if self.cached_loader.load_single_file_with_cache(
                    analyzer, file_path, force_reload
                ):
                    successful_loads += 1
                else:
                    failed_loads += 1
            else:
                print(f"File not found: {file_path}")
                failed_loads += 1

        # Run analysis if needed
        if successful_loads > 0:
            # Check if any files need analysis
            uncached_files = [
                f
                for f in file_paths
                if not self.db_service.is_file_cached(f) or force_reload
            ]

            if uncached_files:
                try:
                    analyzer.analyze_all_data()
                    # Cache the results
                    self.cached_loader.cache_analysis_results(analyzer, uncached_files)
                except Exception as e:
                    print(f"Analysis failed: {e}")
                    raise

        return analyzer, successful_loads, failed_loads

    def get_file_metadata_quick(self, file_path: str) -> Optional[Dict]:
        """
        Quickly get metadata for a file without loading it

        Args:
            file_path (str): Path to the file

        Returns:
            dict or None: File metadata if cached
        """
        return self.db_service.get_file_metadata(file_path)

    def is_file_analyzed(self, file_path: str) -> bool:
        """
        Check if a file has been analyzed and cached

        Args:
            file_path (str): Path to the file

        Returns:
            bool: True if file is analyzed and cached
        """
        return self.db_service.is_file_cached(file_path)

    def scan_directory_for_new_files(self, directory_path: str) -> List[str]:
        """
        Scan a directory for new files that aren't in the cache yet

        Args:
            directory_path (str): Directory to scan

        Returns:
            list: List of new file paths found
        """
        from .data_loader_service import find_input_files

        all_files = find_input_files(directory_path)
        cached_files = {f["file_path"] for f in self.get_available_files()}

        new_files = []
        for file_path in all_files:
            abs_path = os.path.abspath(file_path)
            if abs_path not in cached_files:
                new_files.append(file_path)

        return new_files

    def add_files_to_cache(self, file_paths: List[str]) -> Tuple[int, int]:
        """
        Add new files to the cache (metadata only, no analysis)

        Args:
            file_paths (list): List of file paths to add

        Returns:
            tuple: (successful_adds, failed_adds)
        """
        from .data_loader_service import extract_metadata_from_filename

        successful_adds = 0
        failed_adds = 0

        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    metadata = extract_metadata_from_filename(filename)
                    self.db_service.register_file(file_path, metadata)
                    successful_adds += 1
                else:
                    failed_adds += 1
            except Exception as e:
                print(f"Failed to add {file_path}: {e}")
                failed_adds += 1

        return successful_adds, failed_adds

    def get_gui_file_tree_data(self) -> Dict:
        """
        Get data structured for GUI tree/list views

        Returns:
            dict: Hierarchical data structure for GUI display
        """
        participants = self.get_files_by_participant()

        tree_data = {"participants": {}, "summary": self.get_file_summary_stats()}

        for participant_id, files in participants.items():
            # Group files by condition for this participant
            conditions = {}
            for file_record in files:
                condition = file_record["condition"]
                if condition not in conditions:
                    conditions[condition] = []

                # Add GUI-friendly file info
                file_info = {
                    "filename": os.path.basename(file_record["file_path"]),
                    "full_path": file_record["file_path"],
                    "condition": condition,
                    "timepoint": file_record["timepoint"],
                    "is_analyzed": self.is_file_analyzed(file_record["file_path"]),
                    "file_size_mb": round(file_record["file_size"] / (1024 * 1024), 2),
                    "last_modified": file_record["last_modified"],
                }
                conditions[condition].append(file_info)

            tree_data["participants"][participant_id] = {
                "conditions": conditions,
                "total_files": len(files),
                "analyzed_files": sum(
                    1 for f in files if self.is_file_analyzed(f["file_path"])
                ),
            }

        return tree_data

    def cleanup_cache(self):
        """Clean up orphaned cache entries"""
        self.db_service.cleanup_orphaned_records()

    def get_cache_database_path(self) -> str:
        """Get the path to the cache database file"""
        return self.db_service.db_path


# Convenience functions for GUI integration
def get_gui_service(db_path: str = "granger_cache.db") -> GUIIntegrationService:
    """Get a GUI integration service instance"""
    return GUIIntegrationService(db_path)


def populate_gui_from_cache(db_path: str = "granger_cache.db") -> Dict:
    """
    Convenience function to get all data needed to populate a GUI

    Args:
        db_path (str): Database path

    Returns:
        dict: Complete data structure for GUI population
    """
    service = GUIIntegrationService(db_path)
    return {
        "file_tree": service.get_gui_file_tree_data(),
        "participants": service.get_files_by_participant(),
        "conditions": service.get_files_by_condition(),
        "stats": service.get_file_summary_stats(),
    }
