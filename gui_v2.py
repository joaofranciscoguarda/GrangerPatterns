#!/usr/bin/env python3
"""
Granger Causality Analysis GUI v2 - With Caching Integration

This version integrates with the caching system for:
- Auto-population of file lists from cache on startup
- Instant metadata display without file parsing
- Analysis status tracking (analyzed vs. not analyzed)
- Efficient loading of only selected files
- Smart detection of new files when browsing directories
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys
from pathlib import Path
import numpy as np
import traceback
from granger_analysis import GrangerCausalityAnalyzer
from visualize_matrix import plot_connectivity_matrix
from visualize_network import plot_network_graph
from visualize_nodal import plot_nodal_metrics
from visualize_pairwise import plot_pairwise_comparison
from visualize_global import plot_global_metrics
import report_generator
import scipy.stats as stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd, MultiComparison
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.power import TTestPower, FTestPower
import warnings
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import pingouin as pg
import re

# Import the new caching services
from services import get_gui_service, get_database_service, get_statistics_gui_service

warnings.filterwarnings("ignore")


class GrangerAnalysisGUIv2:
    def __init__(self, root):
        self.root = root
        self.root.title("Granger Causality Analysis v2 - With Smart Caching")
        self.root.geometry("1200x700")

        # Initialize caching services
        self.gui_service = get_gui_service()
        self.db_service = get_database_service()

        # Variables
        self.analyzer = GrangerCausalityAnalyzer()
        self.selected_files = []  # List of selected file paths
        self.current_cache_data = {}  # Current cache data for display

        # Create main frames
        self.create_cache_info_frame()
        self.create_file_frame()
        self.create_analysis_frame()
        self.create_visualization_frame()

        # Add menu bar
        self._create_menu_bar()

        # Auto-populate from cache on startup
        self.refresh_from_cache()

    def create_cache_info_frame(self):
        """Create frame showing cache statistics and controls"""
        cache_frame = ttk.LabelFrame(self.root, text="Cache Information")
        cache_frame.pack(fill="x", padx=10, pady=5)

        # Cache stats display
        self.cache_stats_frame = ttk.Frame(cache_frame)
        self.cache_stats_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # Cache control buttons
        btn_frame = ttk.Frame(cache_frame)
        btn_frame.pack(side="right", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Refresh Cache", command=self.refresh_from_cache
        ).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Scan Directory", command=self.scan_directory).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="Clear Cache", command=self.clear_cache).pack(
            side="left", padx=2
        )

        # Initialize cache stats labels
        self.cache_stats_labels = {}

    def update_cache_stats_display(self):
        """Update the cache statistics display"""
        # Clear existing labels
        for label in self.cache_stats_labels.values():
            label.destroy()
        self.cache_stats_labels.clear()

        # Get current stats
        stats = self.gui_service.get_file_summary_stats()

        # Create new labels
        stats_text = f"📁 Files: {stats['total_files']} | ✓ Analyzed: {stats['cached_analyses']} | 👥 Participants: {stats['unique_participants']} | 🔄 Conditions: {stats['unique_conditions']}"

        self.cache_stats_labels["main"] = ttk.Label(
            self.cache_stats_frame, text=stats_text
        )
        self.cache_stats_labels["main"].pack(side="left")

        # Show participant and condition lists if reasonable size
        if len(stats["participant_list"]) <= 5:
            participants_text = f"Participants: {', '.join(stats['participant_list'])}"
        else:
            participants_text = f"Participants: {', '.join(stats['participant_list'][:3])}... (+{len(stats['participant_list'])-3} more)"

        conditions_text = f"Conditions: {', '.join(stats['condition_list'])}"

        details_text = f" | {participants_text} | {conditions_text}"
        self.cache_stats_labels["details"] = ttk.Label(
            self.cache_stats_frame, text=details_text, font=("TkDefaultFont", 8)
        )
        self.cache_stats_labels["details"].pack(side="left", padx=(10, 0))

    def create_file_frame(self):
        """Create the enhanced file selection frame with caching"""
        file_frame = ttk.LabelFrame(self.root, text="File Management")
        file_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top button frame
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(pady=5, fill="x")

        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(
            side="left", padx=5
        )
        ttk.Button(
            btn_frame, text="Load Selected", command=self.load_selected_files
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Select All", command=self.select_all_files).pack(
            side="left", padx=5
        )
        ttk.Button(
            btn_frame, text="Clear Selection", command=self.clear_selection
        ).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(file_frame)
        filter_frame.pack(fill="x", pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)

        ttk.Label(filter_frame, text="Participant:").pack(side="left", padx=(20, 5))
        self.filter_participant = tk.StringVar()
        self.participant_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_participant, width=10
        )
        self.participant_combo.pack(side="left", padx=5)
        self.participant_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        ttk.Label(filter_frame, text="Condition:").pack(side="left", padx=(20, 5))
        self.filter_condition = tk.StringVar()
        self.condition_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_condition, width=10
        )
        self.condition_combo.pack(side="left", padx=5)
        self.condition_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        ttk.Label(filter_frame, text="Status:").pack(side="left", padx=(20, 5))
        self.filter_status = tk.StringVar()
        status_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_status, width=10
        )
        status_combo["values"] = ("All", "Analyzed", "Not Analyzed")
        status_combo.set("All")
        status_combo.pack(side="left", padx=5)
        status_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(
            side="left", padx=(20, 5)
        )

        # File tree with enhanced columns
        tree_frame = ttk.Frame(file_frame)
        tree_frame.pack(fill="both", expand=True, pady=5)

        # Enhanced columns for better information display
        columns = (
            "Filename",
            "Participant",
            "Condition",
            "Timepoint",
            "Group",
            "Status",
            "Size (MB)",
            "Modified",
            "file_path",  # Hidden column to store file path
        )
        self.file_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")

        # Configure columns
        self.file_tree.heading("#0", text="Select")
        self.file_tree.column("#0", width=50, minwidth=50)

        column_widths = {
            "Filename": 250,
            "Participant": 80,
            "Condition": 80,
            "Timepoint": 80,
            "Group": 60,
            "Status": 80,
            "Size (MB)": 80,
            "Modified": 120,
            "file_path": 0,  # Hidden column
        }

        for col in columns:
            if col == "file_path":
                # Hide the file_path column
                self.file_tree.column(col, width=0, minwidth=0, stretch=False)
                self.file_tree.heading(col, text="")
            else:
                self.file_tree.heading(col, text=col)
                width = column_widths.get(col, 100)
                self.file_tree.column(
                    col, width=width, anchor="center" if col != "Filename" else "w"
                )

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.file_tree.xview
        )
        self.file_tree.configure(xscrollcommand=x_scroll.set)

        # Pack tree and scrollbars
        self.file_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")

        # Bind events
        self.file_tree.bind("<Button-1>", self.on_tree_click)
        self.file_tree.bind("<Double-1>", self.edit_file_metadata)

        # Selection info frame
        selection_frame = ttk.Frame(file_frame)
        selection_frame.pack(fill="x", pady=5)

        self.selection_label = ttk.Label(selection_frame, text="No files selected")
        self.selection_label.pack(side="left")

        # Metadata edit frame (initially hidden)
        self.metadata_frame = ttk.LabelFrame(file_frame, text="Edit Metadata")
        self.create_metadata_edit_form()

    def create_metadata_edit_form(self):
        """Create the metadata editing form"""
        form_frame = ttk.Frame(self.metadata_frame)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Create form fields
        ttk.Label(form_frame, text="Participant ID:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.participant_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.participant_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )

        ttk.Label(form_frame, text="Condition:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.condition_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.condition_var).grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        ttk.Label(form_frame, text="Timepoint:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.timepoint_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.timepoint_var).grid(
            row=2, column=1, sticky="ew", padx=5, pady=5
        )

        ttk.Label(form_frame, text="Group:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.group_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.group_var).grid(
            row=3, column=1, sticky="ew", padx=5, pady=5
        )

        # Buttons
        btn_frame = ttk.Frame(self.metadata_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Save", command=self.save_metadata).pack(
            side="left", padx=5
        )
        ttk.Button(
            btn_frame, text="Cancel", command=lambda: self.metadata_frame.pack_forget()
        ).pack(side="left", padx=5)

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

    def create_analysis_frame(self):
        """Create the analysis options frame"""
        analysis_frame = ttk.LabelFrame(self.root, text="Analysis Options")
        analysis_frame.pack(fill="x", padx=10, pady=5)

        # Analysis buttons
        btn_frame = ttk.Frame(analysis_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Analyze Selected", command=self.analyze_selected
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Generate Tables", command=self.generate_tables
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Statistics", command=self.create_stats_frame).pack(
            side="left", padx=5
        )

        # Analysis status
        self.analysis_status = ttk.Label(analysis_frame, text="Ready to analyze")
        self.analysis_status.pack(side="left", padx=(20, 5))

    def create_visualization_frame(self):
        """Create the visualization options frame"""
        viz_frame = ttk.LabelFrame(self.root, text="Visualization")
        viz_frame.pack(fill="x", padx=10, pady=5)

        # Visualization type selection
        options_frame = ttk.Frame(viz_frame)
        options_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(options_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.metric_type = tk.StringVar(value="All")
        metric_type_combo = ttk.Combobox(options_frame, textvariable=self.metric_type)
        metric_type_combo["values"] = (
            "All",
            "Global",
            "Nodal",
            "Network",
            "Pairwise",
            "Matrix",
        )
        metric_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Visualization buttons
        btn_frame = ttk.Frame(viz_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame,
            text="Generate Visualizations",
            command=self.generate_visualization,
        ).pack(side="left", padx=5)

        # Configure grid weights
        options_frame.columnconfigure(1, weight=1)

    def refresh_from_cache(self):
        """Refresh the GUI from cached data"""
        try:
            # Update cache stats
            self.update_cache_stats_display()

            # Get tree data from cache
            tree_data = self.gui_service.get_gui_file_tree_data()
            self.current_cache_data = tree_data

            # Clear existing tree
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)

            # Populate tree with cached data
            for participant_id, participant_data in tree_data["participants"].items():
                # Create participant node
                participant_node = self.file_tree.insert(
                    "",
                    "end",
                    text="",
                    values=(
                        f"📁 Participant {participant_id}",
                        "",
                        "",
                        "",
                        "",
                        f"{participant_data['analyzed_files']}/{participant_data['total_files']} analyzed",
                        "",
                        "",
                    ),
                )

                for condition, files in participant_data["conditions"].items():
                    # Create condition node
                    analyzed_count = sum(1 for f in files if f["is_analyzed"])
                    condition_node = self.file_tree.insert(
                        participant_node,
                        "end",
                        text="",
                        values=(
                            f"📂 {condition}",
                            "",
                            condition,
                            "",
                            "",
                            f"{analyzed_count}/{len(files)} analyzed",
                            "",
                            "",
                        ),
                    )

                    # Add files under condition
                    for file_info in files:
                        status = (
                            "✓ Analyzed" if file_info["is_analyzed"] else "○ Pending"
                        )
                        modified_time = (
                            pd.to_datetime(
                                file_info["last_modified"], unit="s"
                            ).strftime("%Y-%m-%d %H:%M")
                            if file_info["last_modified"]
                            else ""
                        )

                        file_item = self.file_tree.insert(
                            condition_node,
                            "end",
                            text="☐",
                            values=(
                                file_info["filename"],
                                participant_id,
                                condition,
                                file_info["timepoint"],
                                "",
                                status,
                                file_info["file_size_mb"],
                                modified_time,
                                file_info["full_path"],  # file_path column
                            ),
                        )

            # Update filter dropdowns
            self.update_filter_options()

            # Update selection display
            self.update_selection_display()

            print(
                f"Refreshed GUI with {tree_data['summary']['total_files']} cached files"
            )

        except Exception as e:
            messagebox.showerror(
                "Cache Error", f"Error refreshing from cache: {str(e)}"
            )
            traceback.print_exc()

    def update_filter_options(self):
        """Update the filter dropdown options based on current data"""
        if not self.current_cache_data:
            return

        # Update participant filter
        participants = ["All"] + list(self.current_cache_data["participants"].keys())
        self.participant_combo["values"] = participants
        if (
            not self.filter_participant.get()
            or self.filter_participant.get() not in participants
        ):
            self.filter_participant.set("All")

        # Update condition filter
        conditions = set(["All"])
        for participant_data in self.current_cache_data["participants"].values():
            conditions.update(participant_data["conditions"].keys())
        self.condition_combo["values"] = sorted(list(conditions))
        if (
            not self.filter_condition.get()
            or self.filter_condition.get() not in conditions
        ):
            self.filter_condition.set("All")

    def apply_filters(self, event=None):
        """Apply filters to the file tree display"""
        participant_filter = self.filter_participant.get()
        condition_filter = self.filter_condition.get()
        status_filter = self.filter_status.get()

        # Clear current tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not self.current_cache_data:
            return

        # Apply filters and rebuild tree
        for participant_id, participant_data in self.current_cache_data[
            "participants"
        ].items():
            if participant_filter != "All" and participant_id != participant_filter:
                continue

            # Check if any conditions match the filter
            matching_conditions = {}
            for condition, files in participant_data["conditions"].items():
                if condition_filter != "All" and condition != condition_filter:
                    continue

                # Apply status filter
                filtered_files = []
                for file_info in files:
                    if status_filter == "Analyzed" and not file_info["is_analyzed"]:
                        continue
                    elif status_filter == "Not Analyzed" and file_info["is_analyzed"]:
                        continue
                    filtered_files.append(file_info)

                if filtered_files:
                    matching_conditions[condition] = filtered_files

            if matching_conditions:
                # Create participant node
                total_files = sum(len(files) for files in matching_conditions.values())
                analyzed_files = sum(
                    sum(1 for f in files if f["is_analyzed"])
                    for files in matching_conditions.values()
                )

                participant_node = self.file_tree.insert(
                    "",
                    "end",
                    text="",
                    values=(
                        f"📁 Participant {participant_id}",
                        "",
                        "",
                        "",
                        "",
                        f"{analyzed_files}/{total_files} analyzed",
                        "",
                        "",
                    ),
                )

                for condition, files in matching_conditions.items():
                    # Create condition node
                    analyzed_count = sum(1 for f in files if f["is_analyzed"])
                    condition_node = self.file_tree.insert(
                        participant_node,
                        "end",
                        text="",
                        values=(
                            f"📂 {condition}",
                            "",
                            condition,
                            "",
                            "",
                            f"{analyzed_count}/{len(files)} analyzed",
                            "",
                            "",
                        ),
                    )

                    # Add files
                    for file_info in files:
                        status = (
                            "✓ Analyzed" if file_info["is_analyzed"] else "○ Pending"
                        )
                        modified_time = (
                            pd.to_datetime(
                                file_info["last_modified"], unit="s"
                            ).strftime("%Y-%m-%d %H:%M")
                            if file_info["last_modified"]
                            else ""
                        )

                        file_item = self.file_tree.insert(
                            condition_node,
                            "end",
                            text="☐",
                            values=(
                                file_info["filename"],
                                participant_id,
                                condition,
                                file_info["timepoint"],
                                "",
                                status,
                                file_info["file_size_mb"],
                                modified_time,
                                file_info["full_path"],  # file_path column
                            ),
                        )

    def clear_filters(self):
        """Clear all filters and show all files"""
        self.filter_participant.set("All")
        self.filter_condition.set("All")
        self.filter_status.set("All")
        self.refresh_from_cache()

    def on_tree_click(self, event):
        """Handle tree item selection"""
        item = self.file_tree.identify("item", event.x, event.y)
        if not item:
            return

        # Check if it's a file item (has file_path)
        if self.file_tree.set(item, "file_path"):
            # Toggle selection
            current_text = self.file_tree.item(item, "text")
            file_path = self.file_tree.set(item, "file_path")

            if current_text == "☐":  # Not selected
                self.file_tree.item(item, text="☑")
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
            else:  # Selected
                self.file_tree.item(item, text="☐")
                if file_path in self.selected_files:
                    self.selected_files.remove(file_path)

            self.update_selection_display()

    def select_all_files(self):
        """Select all visible files"""
        self.selected_files.clear()

        def select_recursive(item):
            if self.file_tree.set(item, "file_path"):
                # It's a file
                self.file_tree.item(item, text="☑")
                file_path = self.file_tree.set(item, "file_path")
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)

            # Process children
            for child in self.file_tree.get_children(item):
                select_recursive(child)

        # Process all top-level items
        for item in self.file_tree.get_children():
            select_recursive(item)

        self.update_selection_display()

    def clear_selection(self):
        """Clear all file selections"""
        self.selected_files.clear()

        def clear_recursive(item):
            if self.file_tree.set(item, "file_path"):
                # It's a file
                self.file_tree.item(item, text="☐")

            # Process children
            for child in self.file_tree.get_children(item):
                clear_recursive(child)

        # Process all top-level items
        for item in self.file_tree.get_children():
            clear_recursive(item)

        self.update_selection_display()

    def update_selection_display(self):
        """Update the selection information display"""
        count = len(self.selected_files)
        if count == 0:
            self.selection_label.config(text="No files selected")
        elif count == 1:
            filename = os.path.basename(self.selected_files[0])
            self.selection_label.config(text=f"1 file selected: {filename}")
        else:
            self.selection_label.config(text=f"{count} files selected")

    def add_files(self):
        """Add new files to the cache"""
        filetypes = [
            ("Excel files", "*.xlsx"),
            ("CSV files", "*.csv"),
            ("All files", "*.*"),
        ]
        files = filedialog.askopenfilenames(
            title="Select data files", filetypes=filetypes
        )

        if not files:
            return

        # Add files to cache
        successful_adds, failed_adds = self.gui_service.add_files_to_cache(files)

        if successful_adds > 0:
            messagebox.showinfo(
                "Files Added", f"Successfully added {successful_adds} files to cache"
            )
            self.refresh_from_cache()

        if failed_adds > 0:
            messagebox.showwarning(
                "Some Files Failed", f"{failed_adds} files could not be added"
            )

    def scan_directory(self):
        """Scan a directory for new files"""
        directory = filedialog.askdirectory(
            title="Select directory to scan for new files"
        )

        if not directory:
            return

        # Scan for new files
        new_files = self.gui_service.scan_directory_for_new_files(directory)

        if not new_files:
            messagebox.showinfo(
                "No New Files", "No new files found in the selected directory"
            )
            return

        # Ask user if they want to add the new files
        response = messagebox.askyesno(
            "New Files Found",
            f"Found {len(new_files)} new files.\n\nDo you want to add them to the cache?",
        )

        if response:
            successful_adds, failed_adds = self.gui_service.add_files_to_cache(
                new_files
            )

            if successful_adds > 0:
                messagebox.showinfo(
                    "Files Added", f"Successfully added {successful_adds} new files"
                )
                self.refresh_from_cache()

            if failed_adds > 0:
                messagebox.showwarning(
                    "Some Files Failed", f"{failed_adds} files could not be added"
                )

    def clear_cache(self):
        """Clear the cache after user confirmation"""
        response = messagebox.askyesno(
            "Confirm Clear Cache",
            "This will remove all cached file information and analysis results.\n\n"
            "Are you sure you want to continue?",
        )

        if response:
            # Clean up cache
            self.gui_service.cleanup_cache()

            # Reinitialize database
            from services import init_database

            init_database()

            messagebox.showinfo("Cache Cleared", "Cache has been cleared successfully")
            self.refresh_from_cache()

    def load_selected_files(self):
        """Load the selected files for analysis"""
        if not self.selected_files:
            messagebox.showwarning("No Files Selected", "Please select files to load")
            return

        try:
            self.analysis_status.config(text="Loading selected files...")
            self.root.update()

            # Use the GUI service to load selected files efficiently
            self.analyzer, successful, failed = self.gui_service.load_selected_files(
                self.selected_files
            )

            if successful > 0:
                self.analysis_status.config(
                    text=f"Loaded {successful} files successfully"
                )
                messagebox.showinfo(
                    "Load Complete", f"Successfully loaded {successful} files"
                )

                # Refresh display to show updated analysis status
                self.refresh_from_cache()
            else:
                self.analysis_status.config(text="No files loaded")
                messagebox.showwarning("Load Failed", "No files could be loaded")

        except Exception as e:
            self.analysis_status.config(text="Load failed")
            messagebox.showerror("Load Error", f"Error loading files: {str(e)}")
            traceback.print_exc()

    def analyze_selected(self):
        """Analyze the currently loaded data"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Data Loaded", "Please load files first")
            return

        try:
            self.analysis_status.config(text="Running analysis...")
            self.root.update()

            # Check if any files in the analyzer need to be analyzed and cached
            uncached_files = []
            for analysis_key, analysis_data in self.analyzer.analyses.items():
                # Try to find the original file path
                for file_path in self.selected_files:
                    metadata = self.gui_service.get_file_metadata_quick(file_path)
                    if metadata:
                        key = f"{metadata['participant_id']}_{metadata['condition']}_{metadata['timepoint']}"
                        if key == analysis_key and not self.db_service.is_file_cached(file_path):
                            uncached_files.append(file_path)
                            break

            # If there are uncached files, run analysis and cache results
            if uncached_files:
                print(f"Analyzing and caching {len(uncached_files)} files...")
                self.analyzer.analyze_all_data()
                
                # Cache the results
                self.gui_service.cached_loader.cache_analysis_results(
                    self.analyzer, uncached_files
                )
                print("✓ Analysis results cached")

            analysis_count = len(self.analyzer.analyses)
            self.analysis_status.config(
                text=f"Analysis complete - {analysis_count} analyses ready"
            )

            messagebox.showinfo(
                "Analysis Complete", f"Successfully analyzed {analysis_count} files"
            )

            # Refresh to show updated status
            self.refresh_from_cache()

        except Exception as e:
            self.analysis_status.config(text="Analysis failed")
            messagebox.showerror("Analysis Error", f"Error during analysis: {str(e)}")
            traceback.print_exc()

    def edit_file_metadata(self, event):
        """Edit metadata for a selected file"""
        item = self.file_tree.selection()
        if not item:
            return

        item = item[0]
        file_path = self.file_tree.set(item, "file_path")

        if not file_path:
            return  # Not a file item

        # Get current metadata
        metadata = self.gui_service.get_file_metadata_quick(file_path)
        if not metadata:
            messagebox.showwarning("No Metadata", "No metadata found for this file")
            return

        # Populate form
        self.selected_item_for_edit = item
        self.participant_var.set(metadata.get("participant_id", ""))
        self.condition_var.set(metadata.get("condition", ""))
        self.timepoint_var.set(metadata.get("timepoint", ""))
        self.group_var.set(metadata.get("group_info", ""))

        # Show metadata frame
        self.metadata_frame.pack(fill="x", padx=10, pady=5, after=self.file_tree.master)

    def save_metadata(self):
        """Save edited metadata"""
        if not hasattr(self, "selected_item_for_edit"):
            return

        file_path = self.file_tree.set(self.selected_item_for_edit, "file_path")

        # Update metadata in database
        new_metadata = {
            "participant_id": self.participant_var.get(),
            "condition": self.condition_var.get(),
            "timepoint": self.timepoint_var.get(),
            "group_info": self.group_var.get(),
        }

        try:
            # Update in database
            self.db_service.register_file(file_path, new_metadata)

            messagebox.showinfo("Metadata Updated", "File metadata has been updated")

            # Hide metadata frame and refresh display
            self.metadata_frame.pack_forget()
            self.refresh_from_cache()

        except Exception as e:
            messagebox.showerror("Update Error", f"Error updating metadata: {str(e)}")

    def generate_tables(self):
        """Generate and export tables based on the analyzed data"""
        if not self.analyzer.analyses:
            messagebox.showwarning(
                "No Analyses", "No analyses available. Please analyze data first."
            )
            return

        # Ask for grouping type
        groupby = self._ask_groupby()
        if not groupby:
            return

        try:
            # Generate tables
            tables = self.analyzer.create_group_tables(groupby=groupby)

            if not tables:
                messagebox.showwarning("No Tables", "No tables could be generated.")
                return

            # Ask for export directory
            export_dir = filedialog.askdirectory(
                title="Select directory for table export"
            )
            if not export_dir:
                return

            # Export tables
            saved_files = self.analyzer.export_tables_to_csv(
                tables, output_dir=export_dir
            )

            if saved_files:
                messagebox.showinfo(
                    "Export Complete",
                    f"Exported {len(saved_files)} tables to {export_dir}",
                )
            else:
                messagebox.showwarning("Export Failed", "No tables were exported.")

        except Exception as e:
            messagebox.showerror(
                "Table Generation Error", f"Error generating tables: {str(e)}"
            )

    def generate_visualization(self):
        """Generate visualizations for the analyzed data"""
        if not self.analyzer.analyses:
            messagebox.showwarning(
                "No Analyses", "No analyses available. Please analyze data first."
            )
            return

        # Get selected metric type
        selected_metric_type = self.metric_type.get()

        # Ask for output directory
        output_dir = filedialog.askdirectory(
            title="Select directory for visualization output"
        )
        if not output_dir:
            return

        # Use the existing visualization generation logic from the original GUI
        # This would be the same as in the original GUI
        try:
            # Create figures directory
            figures_dir = os.path.join(output_dir, "figures")
            os.makedirs(figures_dir, exist_ok=True)

            # Generate visualizations for each analysis
            for key, analysis in self.analyzer.analyses.items():
                participant_id = analysis["metadata"]["participant_id"]
                timepoint = analysis["metadata"]["timepoint"]
                condition = analysis["metadata"]["condition"]

                base_name = f"{participant_id}_{timepoint}_{condition}"

                # Generate based on selected metric type
                if selected_metric_type in ["All", "Matrix"]:
                    plot_connectivity_matrix(
                        analysis["connectivity_matrix"],
                        f"Connectivity Matrix: {participant_id} {timepoint} {condition}",
                        os.path.join(figures_dir, f"{base_name}_matrix.png"),
                    )

                if selected_metric_type in ["All", "Network"]:
                    G = self.analyzer.create_network_graph(key)
                    plot_network_graph(
                        G,
                        f"Network Graph: {participant_id} {timepoint} {condition}",
                        os.path.join(figures_dir, f"{base_name}_network.png"),
                    )

                if selected_metric_type in ["All", "Global"]:
                    plot_global_metrics(
                        analysis["global"],
                        f"Global Metrics: {participant_id} {timepoint} {condition}",
                        os.path.join(figures_dir, f"{base_name}_global.png"),
                    )

                if selected_metric_type in ["All", "Nodal"]:
                    plot_nodal_metrics(
                        analysis["nodal"],
                        f"Nodal Metrics: {participant_id} {timepoint} {condition}",
                        os.path.join(figures_dir, f"{base_name}_nodal.png"),
                    )

                if selected_metric_type in ["All", "Pairwise"]:
                    plot_pairwise_comparison(
                        analysis["pairwise"],
                        f"Pairwise Connections: {participant_id} {timepoint} {condition}",
                        os.path.join(figures_dir, f"{base_name}_pairwise.png"),
                    )

            analysis_count = len(self.analyzer.analyses)
            messagebox.showinfo(
                "Visualization Complete",
                f"Generated visualizations for {analysis_count} analyses in {figures_dir}",
            )

        except Exception as e:
            messagebox.showerror(
                "Visualization Error", f"Error generating visualizations: {str(e)}"
            )
            traceback.print_exc()

    def create_stats_frame(self):
        """Create the statistical analysis frame with full functionality"""
        if not self.analyzer.analyses:
            messagebox.showwarning(
                "No Analyses",
                "No analyses available. Please load and analyze data first.",
            )
            return

        # Create a new window for statistical analysis
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistical Analysis")
        stats_window.geometry("1200x800")
        stats_window.transient(self.root)

        # Create the statistics GUI service
        stats_gui = get_statistics_gui_service(stats_window, self.analyzer)

        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        outlier_tab = ttk.Frame(notebook)
        normality_tab = ttk.Frame(notebook)
        assumption_tab = ttk.Frame(notebook)
        anova_tab = ttk.Frame(notebook)
        posthoc_tab = ttk.Frame(notebook)
        paired_test_tab = ttk.Frame(notebook)

        notebook.add(outlier_tab, text="Outlier Detection")
        notebook.add(normality_tab, text="Normality Tests")
        notebook.add(assumption_tab, text="Assumption Tests")
        notebook.add(anova_tab, text="ANOVA")
        notebook.add(posthoc_tab, text="Post-hoc Tests")
        notebook.add(paired_test_tab, text="Paired Tests")

        # Create tab content using the statistics GUI service
        stats_gui.create_outlier_tab(outlier_tab)
        stats_gui.create_normality_tab(normality_tab)
        stats_gui.create_assumption_tab(assumption_tab)
        stats_gui.create_anova_tab(anova_tab)
        stats_gui.create_posthoc_tab(posthoc_tab)
        stats_gui.create_paired_test_tab(paired_test_tab)

        # Add a status bar
        status_frame = ttk.Frame(stats_window)
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        stats_info = (
            f"Loaded {len(self.analyzer.analyses)} analyses for statistical testing"
        )
        ttk.Label(status_frame, text=stats_info).pack(side="left")

        # Close button
        ttk.Button(status_frame, text="Close", command=stats_window.destroy).pack(
            side="right"
        )

    def _ask_groupby(self):
        """Ask user for groupby option"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Group By")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select grouping option:").pack(pady=10)

        groupby_var = tk.StringVar()

        ttk.Radiobutton(
            dialog, text="By Condition", value="condition", variable=groupby_var
        ).pack(anchor="w", padx=20)
        ttk.Radiobutton(
            dialog, text="By Timepoint", value="timepoint", variable=groupby_var
        ).pack(anchor="w", padx=20)
        ttk.Radiobutton(
            dialog, text="By Participant", value="participant", variable=groupby_var
        ).pack(anchor="w", padx=20)
        ttk.Radiobutton(
            dialog,
            text="By Condition × Timepoint",
            value="condition_timepoint",
            variable=groupby_var,
        ).pack(anchor="w", padx=20)

        result = [None]

        def on_ok():
            result[0] = groupby_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=on_ok).pack(
            side="right", padx=10, pady=10
        )
        ttk.Button(dialog, text="Cancel", command=on_cancel).pack(
            side="right", padx=10, pady=10
        )

        # Wait for dialog to be closed
        self.root.wait_window(dialog)

        return result[0]

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Files", command=self.add_files)
        file_menu.add_command(label="Scan Directory", command=self.scan_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Refresh Cache", command=self.refresh_from_cache)
        file_menu.add_command(label="Clear Cache", command=self.clear_cache)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(
            label="Load Selected Files", command=self.load_selected_files
        )
        analysis_menu.add_command(
            label="Analyze Selected", command=self.analyze_selected
        )
        analysis_menu.add_command(label="Generate Tables", command=self.generate_tables)
        analysis_menu.add_separator()
        analysis_menu.add_command(
            label="Open Statistics Window", command=self.create_stats_frame
        )
        menubar.add_cascade(label="Analysis", menu=analysis_menu)

        # Visualization menu
        viz_menu = tk.Menu(menubar, tearoff=0)
        viz_menu.add_command(
            label="Generate Visualizations", command=self.generate_visualization
        )
        menubar.add_cascade(label="Visualization", menu=viz_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Select All Files", command=self.select_all_files)
        view_menu.add_command(label="Clear Selection", command=self.clear_selection)
        view_menu.add_command(label="Clear Filters", command=self.clear_filters)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Set the menu
        self.root.config(menu=menubar)

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Granger Causality Analysis GUI v2\n\n"
            "Features:\n"
            "• Smart caching for fast startup\n"
            "• Instant metadata display\n"
            "• Efficient file loading\n"
            "• Analysis status tracking\n"
            "• Advanced filtering and selection\n\n"
            "Built with caching integration services",
        )


def main():
    # Initialize the database on startup
    try:
        from services import init_database

        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

    root = tk.Tk()
    app = GrangerAnalysisGUIv2(root)
    root.mainloop()


if __name__ == "__main__":
    main()
