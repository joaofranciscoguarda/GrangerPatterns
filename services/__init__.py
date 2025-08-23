#!/usr/bin/env python3
"""
Services Package for Granger Causality Analysis

This package contains modular services for data loading, visualization, and reporting.
"""

# Import main service functions for easy access
from .data_loader_service import (
    load_and_analyze_files,
    group_analyses_by_participant,
    group_analyses_by_condition,
)

from .matrix_visualization_service import (
    generate_individual_matrix_visualizations,
    generate_condition_level_matrix_visualizations,
)

from .network_visualization_service import (
    generate_individual_network_visualizations,
    generate_condition_level_network_visualizations,
)

from .nodal_visualization_service import (
    generate_individual_nodal_visualizations,
    generate_condition_level_nodal_visualizations,
)

from .pairwise_visualization_service import (
    generate_individual_pairwise_visualizations,
    generate_condition_level_pairwise_visualizations,
)

from .global_visualization_service import (
    generate_individual_global_visualizations,
    generate_condition_level_global_visualizations,
)

from .report_service import (
    generate_matrix_analysis_report,
    generate_network_analysis_report,
    generate_nodal_analysis_report,
    generate_pairwise_analysis_report,
    generate_global_analysis_report,
)

from .file_system_service import (
    create_matrix_output_directories,
    create_network_output_directories,
    create_nodal_output_directories,
    create_pairwise_output_directories,
    create_global_output_directories,
    validate_input_directory,
)

# New database and caching services
from .database_service import (
    DatabaseService,
    get_database_service,
    init_database,
)

from .cached_data_loader_service import (
    CachedDataLoaderService,
    get_cached_data_loader,
    load_files_with_cache,
)

# GUI integration service
from .gui_integration_service import (
    GUIIntegrationService,
    get_gui_service,
    populate_gui_from_cache,
)

__all__ = [
    # Data loading
    "load_and_analyze_files",
    "group_analyses_by_participant",
    "group_analyses_by_condition",
    # Matrix visualization
    "generate_individual_matrix_visualizations",
    "generate_condition_level_matrix_visualizations",
    # Network visualization
    "generate_individual_network_visualizations",
    "generate_condition_level_network_visualizations",
    # Nodal visualization
    "generate_individual_nodal_visualizations",
    "generate_condition_level_nodal_visualizations",
    # Pairwise visualization
    "generate_individual_pairwise_visualizations",
    "generate_condition_level_pairwise_visualizations",
    # Global visualization
    "generate_individual_global_visualizations",
    "generate_condition_level_global_visualizations",
    # Report generation
    "generate_matrix_analysis_report",
    "generate_network_analysis_report",
    "generate_nodal_analysis_report",
    "generate_pairwise_analysis_report",
    "generate_global_analysis_report",
    # File system operations
    "create_matrix_output_directories",
    "create_network_output_directories",
    "create_nodal_output_directories",
    "create_pairwise_output_directories",
    "create_global_output_directories",
    "validate_input_directory",
    # Database services
    "DatabaseService",
    "get_database_service",
    "init_database",
    # Cached data loading
    "CachedDataLoaderService",
    "get_cached_data_loader",
    "load_files_with_cache",
    # GUI integration
    "GUIIntegrationService",
    "get_gui_service",
    "populate_gui_from_cache",
]
