#!/usr/bin/env python3
"""
Database Service for Granger Causality Analysis

This service handles SQLite database operations for caching file information,
metadata, and analysis results to prevent redundant processing.
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd


class DatabaseService:
    """Service for managing SQLite database operations"""

    def __init__(self, db_path: str = "granger_cache.db"):
        """
        Initialize the database service

        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create files table for tracking processed files
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    last_modified REAL NOT NULL,
                    participant_id TEXT,
                    condition TEXT,
                    timepoint TEXT,
                    group_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create analysis_results table for caching analysis outcomes
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    connectivity_matrix TEXT,  -- JSON serialized matrix
                    global_metrics TEXT,       -- JSON serialized global metrics
                    electrode_list TEXT,       -- JSON serialized electrode list
                    analysis_params TEXT,      -- JSON serialized analysis parameters
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id),
                    UNIQUE(file_id, analysis_type)
                )
            """
            )

            # Create index for faster lookups
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_path ON files (file_path)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_hash ON files (file_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_analysis_file ON analysis_results (file_id)"
            )

            conn.commit()

    def _get_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file for change detection

        Args:
            file_path (str): Path to the file

        Returns:
            str: MD5 hash of the file
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""

    def register_file(self, file_path: str, metadata: Dict) -> int:
        """
        Register a file in the database with its metadata

        Args:
            file_path (str): Path to the file
            metadata (dict): Extracted metadata (participant_id, condition, etc.)

        Returns:
            int: File ID in the database
        """
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file stats
        stat = os.stat(file_path)
        file_size = stat.st_size
        last_modified = stat.st_mtime
        file_hash = self._get_file_hash(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if file already exists
            cursor.execute(
                "SELECT id, file_hash, last_modified FROM files WHERE file_path = ?",
                (file_path,),
            )
            existing = cursor.fetchone()

            if existing:
                file_id, existing_hash, existing_modified = existing

                # Check if file has changed
                if existing_hash != file_hash or existing_modified != last_modified:
                    # File has changed, update record
                    cursor.execute(
                        """
                        UPDATE files SET 
                        file_hash = ?, file_size = ?, last_modified = ?,
                        participant_id = ?, condition = ?, timepoint = ?, group_info = ?,
                        updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (
                            file_hash,
                            file_size,
                            last_modified,
                            metadata.get("participant_id"),
                            metadata.get("condition"),
                            metadata.get("timepoint"),
                            metadata.get("group"),
                            file_id,
                        ),
                    )

                    # Clear old analysis results since file changed
                    cursor.execute(
                        "DELETE FROM analysis_results WHERE file_id = ?", (file_id,)
                    )
                    print(f"Updated file record: {file_path}")

                return file_id
            else:
                # Insert new file record
                cursor.execute(
                    """
                    INSERT INTO files (file_path, file_hash, file_size, last_modified,
                                     participant_id, condition, timepoint, group_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        file_path,
                        file_hash,
                        file_size,
                        last_modified,
                        metadata.get("participant_id"),
                        metadata.get("condition"),
                        metadata.get("timepoint"),
                        metadata.get("group"),
                    ),
                )

                file_id = cursor.lastrowid
                print(f"Registered new file: {file_path}")
                return file_id

    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        """
        Get cached metadata for a file

        Args:
            file_path (str): Path to the file

        Returns:
            dict or None: Cached metadata if available
        """
        file_path = os.path.abspath(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT participant_id, condition, timepoint, group_info 
                FROM files WHERE file_path = ?
            """,
                (file_path,),
            )

            result = cursor.fetchone()
            if result:
                return {
                    "participant_id": result[0],
                    "condition": result[1],
                    "timepoint": result[2],
                    "group": result[3] or "",
                }
            return None

    def cache_analysis_result(
        self,
        file_path: str,
        analysis_type: str,
        connectivity_matrix: pd.DataFrame,
        global_metrics: Dict = None,
        analysis_params: Dict = None,
    ):
        """
        Cache analysis results for a file

        Args:
            file_path (str): Path to the analyzed file
            analysis_type (str): Type of analysis (e.g., 'granger_causality')
            connectivity_matrix (pd.DataFrame): Resulting connectivity matrix
            global_metrics (dict): Global analysis metrics
            analysis_params (dict): Parameters used for analysis
        """
        file_path = os.path.abspath(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get file ID
            cursor.execute("SELECT id FROM files WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"File not registered: {file_path}")

            file_id = result[0]

            # Serialize data
            matrix_json = connectivity_matrix.to_json(orient="index")
            electrode_list = json.dumps(list(connectivity_matrix.index))
            metrics_json = json.dumps(global_metrics) if global_metrics else None
            params_json = json.dumps(analysis_params) if analysis_params else None

            # Insert or update analysis result
            cursor.execute(
                """
                INSERT OR REPLACE INTO analysis_results 
                (file_id, analysis_type, connectivity_matrix, global_metrics, 
                 electrode_list, analysis_params)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    file_id,
                    analysis_type,
                    matrix_json,
                    metrics_json,
                    electrode_list,
                    params_json,
                ),
            )

            conn.commit()
            print(f"Cached analysis result for: {file_path}")

    def get_cached_analysis(self, file_path: str, analysis_type: str) -> Optional[Dict]:
        """
        Retrieve cached analysis results

        Args:
            file_path (str): Path to the file
            analysis_type (str): Type of analysis

        Returns:
            dict or None: Cached analysis results if available
        """
        file_path = os.path.abspath(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ar.connectivity_matrix, ar.global_metrics, ar.electrode_list, ar.analysis_params
                FROM analysis_results ar
                JOIN files f ON ar.file_id = f.id
                WHERE f.file_path = ? AND ar.analysis_type = ?
            """,
                (file_path, analysis_type),
            )

            result = cursor.fetchone()
            if result:
                matrix_json, metrics_json, electrode_json, params_json = result

                # Deserialize data
                connectivity_matrix = pd.read_json(matrix_json, orient="index")
                electrode_list = json.loads(electrode_json)
                global_metrics = json.loads(metrics_json) if metrics_json else {}
                analysis_params = json.loads(params_json) if params_json else {}

                return {
                    "connectivity_matrix": connectivity_matrix,
                    "global_metrics": global_metrics,
                    "electrode_list": electrode_list,
                    "analysis_params": analysis_params,
                }
            return None

    def is_file_cached(
        self, file_path: str, analysis_type: str = "granger_causality"
    ) -> bool:
        """
        Check if a file has cached analysis results

        Args:
            file_path (str): Path to the file
            analysis_type (str): Type of analysis to check

        Returns:
            bool: True if cached results exist and file hasn't changed
        """
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            return False

        # Check if file has changed since caching
        current_hash = self._get_file_hash(file_path)
        current_modified = os.path.getmtime(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.file_hash, f.last_modified, ar.id
                FROM files f
                LEFT JOIN analysis_results ar ON f.id = ar.file_id AND ar.analysis_type = ?
                WHERE f.file_path = ?
            """,
                (analysis_type, file_path),
            )

            result = cursor.fetchone()
            if result:
                cached_hash, cached_modified, analysis_id = result
                # File is cached if analysis exists and file hasn't changed
                return (
                    analysis_id is not None
                    and cached_hash == current_hash
                    and cached_modified == current_modified
                )
            return False

    def get_all_files(
        self, condition: str = None, participant_id: str = None
    ) -> List[Dict]:
        """
        Get all registered files, optionally filtered

        Args:
            condition (str, optional): Filter by condition
            participant_id (str, optional): Filter by participant ID

        Returns:
            list: List of file records
        """
        query = "SELECT * FROM files WHERE 1=1"
        params = []

        if condition:
            query += " AND condition = ?"
            params.append(condition)

        if participant_id:
            query += " AND participant_id = ?"
            params.append(participant_id)

        query += " ORDER BY participant_id, condition, timepoint"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def cleanup_orphaned_records(self):
        """Remove records for files that no longer exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all file paths
            cursor.execute("SELECT id, file_path FROM files")
            files = cursor.fetchall()

            orphaned_ids = []
            for file_id, file_path in files:
                if not os.path.exists(file_path):
                    orphaned_ids.append(file_id)

            if orphaned_ids:
                # Remove orphaned analysis results
                cursor.execute(
                    f'DELETE FROM analysis_results WHERE file_id IN ({",".join("?" * len(orphaned_ids))})',
                    orphaned_ids,
                )

                # Remove orphaned file records
                cursor.execute(
                    f'DELETE FROM files WHERE id IN ({",".join("?" * len(orphaned_ids))})',
                    orphaned_ids,
                )

                conn.commit()
                print(f"Cleaned up {len(orphaned_ids)} orphaned records")

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count files and analyses
            cursor.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            analysis_count = cursor.fetchone()[0]

            # Get unique participants and conditions
            cursor.execute(
                "SELECT COUNT(DISTINCT participant_id) FROM files WHERE participant_id IS NOT NULL"
            )
            participant_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT condition) FROM files WHERE condition IS NOT NULL"
            )
            condition_count = cursor.fetchone()[0]

            return {
                "total_files": file_count,
                "cached_analyses": analysis_count,
                "unique_participants": participant_count,
                "unique_conditions": condition_count,
                "database_path": self.db_path,
            }


# Convenience functions for easy usage
def get_database_service(db_path: str = "granger_cache.db") -> DatabaseService:
    """Get a database service instance"""
    return DatabaseService(db_path)


def init_database(db_path: str = "granger_cache.db") -> DatabaseService:
    """Initialize database and return service instance"""
    service = DatabaseService(db_path)
    print(f"Database initialized: {db_path}")
    return service
