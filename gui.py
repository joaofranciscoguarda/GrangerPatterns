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
warnings.filterwarnings('ignore')

class FileInfo:
    """Class to store file information"""
    def __init__(self, file_path, participant_id=None, condition=None, timepoint=None):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        
        # Extract metadata from filename
        parts = os.path.splitext(self.filename)[0].split('_')
        
        # Set default values based on filename if available
        if participant_id:
            self.participant_id = participant_id
        elif len(parts) > 0 and parts[0].startswith('UTF-'):
            self.participant_id = parts[0].replace('UTF-', '')
        else:
            self.participant_id = ""
            
        if timepoint:
            self.timepoint = timepoint
        elif len(parts) > 1 and parts[1].startswith('T'):
            self.timepoint = parts[1]
        else:
            self.timepoint = ""
            
        if condition:
            self.condition = condition
        elif len(parts) > 2:
            self.condition = parts[2]
        else:
            self.condition = ""

class GrangerAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Granger Causality Analysis")
        self.root.geometry("1000x650")
        
        self.analyzer = GrangerCausalityAnalyzer()
        
        # Variables
        self.selected_files = []
        self.file_info = []  # List of dicts with file paths and metadata
        
        # Create main frames
        self.create_file_frame()
        self.create_analysis_frame()
        self.create_visualization_frame()
        
        # Add menu bar
        self._create_menu_bar()
        
        # Add a button for statistics in the main interface too
        stats_button = ttk.Button(self.root, text="Open Statistics Window", command=self.create_stats_frame)
        stats_button.pack(pady=10)
        
    def create_file_frame(self):
        """Create the file selection frame"""
        file_frame = ttk.LabelFrame(self.root, text="File Selection")
        file_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Buttons for file selection
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(pady=5, fill="x")
        
        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_files).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_files).pack(side="left", padx=5)
        
        # File list with metadata
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # Create treeview for files
        columns = ("Filename", "Participant", "Condition", "Timepoint", "Status")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.file_tree.heading(col, text=col)
            if col == "Filename":
                self.file_tree.column(col, width=300, stretch=True)
            else:
                self.file_tree.column(col, width=100, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.file_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        
        # Double-click to edit metadata
        self.file_tree.bind("<Double-1>", self.edit_file_metadata)
        
        # Metadata edit frame (initially hidden)
        self.metadata_frame = ttk.LabelFrame(file_frame, text="Edit Metadata")
        
        # Create form fields
        form_frame = ttk.Frame(self.metadata_frame)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Participant ID
        ttk.Label(form_frame, text="Participant ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.participant_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.participant_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Condition
        ttk.Label(form_frame, text="Condition:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.condition_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.condition_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Timepoint
        ttk.Label(form_frame, text="Timepoint:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.timepoint_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.timepoint_var).grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.metadata_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save_metadata).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: self.metadata_frame.pack_forget()).pack(side="left", padx=5)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
    def create_analysis_frame(self):
        """Create the analysis options frame"""
        analysis_frame = ttk.LabelFrame(self.root, text="Analysis Options")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Analysis parameters
        param_frame = ttk.Frame(analysis_frame)
        param_frame.pack(fill="x", padx=10, pady=5)
        
        # Load and analyze buttons
        btn_frame = ttk.Frame(analysis_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Load Data", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Analyze All", command=self.analyze_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Generate Tables", command=self.generate_tables).pack(side="left", padx=5)
        
    def create_visualization_frame(self):
        """Create the visualization options frame"""
        viz_frame = ttk.LabelFrame(self.root, text="Visualization")
        viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Visualization type selection
        options_frame = ttk.Frame(viz_frame)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(options_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.metric_type = tk.StringVar(value="All")
        metric_type_combo = ttk.Combobox(options_frame, textvariable=self.metric_type)
        metric_type_combo['values'] = ('All', 'Global', 'Nodal', 'Network', 'Pairwise', 'Matrix')
        metric_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Visualization buttons
        btn_frame = ttk.Frame(viz_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Generate All Visualizations", command=self.generate_visualization).pack(side="left", padx=5)
        
        # Configure grid weights
        options_frame.columnconfigure(1, weight=1)
    
    def create_stats_frame(self):
        """Create the statistical analysis frame"""
        # Create a new window for statistical analysis
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistical Analysis")
        stats_window.geometry("900x700")
        
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        outlier_tab = ttk.Frame(notebook)
        normality_tab = ttk.Frame(notebook)
        assumption_tab = ttk.Frame(notebook)
        anova_tab = ttk.Frame(notebook)
        posthoc_tab = ttk.Frame(notebook)
        
        notebook.add(outlier_tab, text="Outlier Detection")
        notebook.add(normality_tab, text="Normality Tests")
        notebook.add(assumption_tab, text="Assumption Tests")
        notebook.add(anova_tab, text="ANOVA")
        notebook.add(posthoc_tab, text="Post-hoc Tests")
        
        # Outlier Detection Tab
        self._create_outlier_tab(outlier_tab)
        
        # Normality Test Tab
        self._create_normality_tab(normality_tab)
        
        # Assumption Tests Tab
        self._create_assumption_tab(assumption_tab)
        
        # ANOVA Tab
        self._create_anova_tab(anova_tab)
        
        # Post-hoc Tab
        self._create_posthoc_tab(posthoc_tab)
    
    def _create_outlier_tab(self, parent):
        """Create outlier detection tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.outlier_metric_type = tk.StringVar(value="Global")
        outlier_metric_combo = ttk.Combobox(selection_frame, textvariable=self.outlier_metric_type)
        outlier_metric_combo['values'] = ('Global', 'Nodal', 'Pairwise')
        outlier_metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Variable:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.outlier_variable = tk.StringVar()
        self.outlier_variable_combo = ttk.Combobox(selection_frame, textvariable=self.outlier_variable)
        self.outlier_variable_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Update variables when metric type changes
        outlier_metric_combo.bind("<<ComboboxSelected>>", self._update_outlier_variables)
        
        # Detection method frame
        method_frame = ttk.LabelFrame(parent, text="Detection Method")
        method_frame.pack(fill="x", padx=10, pady=5)
        
        self.outlier_method = tk.StringVar(value="z_score")
        ttk.Radiobutton(method_frame, text="Z-Score (±3 SD)", value="z_score", variable=self.outlier_method).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(method_frame, text="IQR (1.5 × IQR)", value="iqr", variable=self.outlier_method).pack(anchor="w", padx=20, pady=2)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Detect Outliers", command=self._detect_outliers).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Outliers", command=self._remove_outliers).pack(side="left", padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for outlier results
        columns = ("Participant", "Condition", "Timepoint", "Value", "Status")
        self.outlier_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.outlier_tree.heading(col, text=col)
            self.outlier_tree.column(col, width=100, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.outlier_tree.yview)
        self.outlier_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.outlier_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def _create_normality_tab(self, parent):
        """Create normality test tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.normality_metric_type = tk.StringVar(value="Global")
        normality_metric_combo = ttk.Combobox(selection_frame, textvariable=self.normality_metric_type)
        normality_metric_combo['values'] = ('Global', 'Nodal', 'Pairwise')
        normality_metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Variable:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.normality_variable = tk.StringVar()
        self.normality_variable_combo = ttk.Combobox(selection_frame, textvariable=self.normality_variable)
        self.normality_variable_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Grouping frame
        group_frame = ttk.LabelFrame(parent, text="Group By")
        group_frame.pack(fill="x", padx=10, pady=5)
        
        self.normality_group = tk.StringVar(value="none")
        ttk.Radiobutton(group_frame, text="No Grouping", value="none", variable=self.normality_group).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(group_frame, text="Condition", value="condition", variable=self.normality_group).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(group_frame, text="Timepoint", value="timepoint", variable=self.normality_group).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(group_frame, text="Condition × Timepoint", value="both", variable=self.normality_group).pack(anchor="w", padx=20, pady=2)
        
        # Update variables when metric type changes
        normality_metric_combo.bind("<<ComboboxSelected>>", self._update_normality_variables)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Run Shapiro-Wilk Test", command=self._run_normality_test).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self._export_normality_results).pack(side="left", padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for normality results
        columns = ("Group", "N", "W Statistic", "p-value", "Normal")
        self.normality_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.normality_tree.heading(col, text=col)
            self.normality_tree.column(col, width=100, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.normality_tree.yview)
        self.normality_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.normality_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def _create_assumption_tab(self, parent):
        """Create assumption tests tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.assumption_metric_type = tk.StringVar(value="Global")
        assumption_metric_combo = ttk.Combobox(selection_frame, textvariable=self.assumption_metric_type)
        assumption_metric_combo['values'] = ('Global', 'Nodal', 'Pairwise')
        assumption_metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Variable:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.assumption_variable = tk.StringVar()
        self.assumption_variable_combo = ttk.Combobox(selection_frame, textvariable=self.assumption_variable)
        self.assumption_variable_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Update variables when metric type changes
        assumption_metric_combo.bind("<<ComboboxSelected>>", self._update_assumption_variables)
        
        # Test selection frame
        test_frame = ttk.LabelFrame(parent, text="Tests to Run")
        test_frame.pack(fill="x", padx=10, pady=5)
        
        self.test_homogeneity = tk.BooleanVar(value=True)
        ttk.Checkbutton(test_frame, text="Homogeneity of Variance (Levene's Test)", variable=self.test_homogeneity).pack(anchor="w", padx=20, pady=2)
        
        self.test_sphericity = tk.BooleanVar(value=False)
        ttk.Checkbutton(test_frame, text="Sphericity (Mauchly's Test) - for repeated measures", variable=self.test_sphericity).pack(anchor="w", padx=20, pady=2)
        
        self.test_heteroscedasticity = tk.BooleanVar(value=True)
        ttk.Checkbutton(test_frame, text="Heteroscedasticity (Breusch-Pagan Test)", variable=self.test_heteroscedasticity).pack(anchor="w", padx=20, pady=2)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Run Tests", command=self._run_assumption_tests).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self._export_assumption_results).pack(side="left", padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for assumption test results
        columns = ("Test", "Statistic", "p-value", "Passed")
        self.assumption_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.assumption_tree.heading(col, text=col)
            self.assumption_tree.column(col, width=100, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.assumption_tree.yview)
        self.assumption_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.assumption_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def _create_anova_tab(self, parent):
        """Create ANOVA tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.anova_metric_type = tk.StringVar(value="Global")
        anova_metric_combo = ttk.Combobox(selection_frame, textvariable=self.anova_metric_type)
        anova_metric_combo['values'] = ('Global', 'Nodal', 'Pairwise')
        anova_metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Variable:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.anova_variable = tk.StringVar()
        self.anova_variable_combo = ttk.Combobox(selection_frame, textvariable=self.anova_variable)
        self.anova_variable_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Update variables when metric type changes
        anova_metric_combo.bind("<<ComboboxSelected>>", self._update_anova_variables)
        
        # ANOVA Type frame
        type_frame = ttk.LabelFrame(parent, text="ANOVA Type")
        type_frame.pack(fill="x", padx=10, pady=5)
        
        self.anova_type = tk.StringVar(value="factorial")
        ttk.Radiobutton(type_frame, text="Factorial ANOVA (Between-subjects)", value="factorial", variable=self.anova_type).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(type_frame, text="Repeated Measures ANOVA", value="repeated", variable=self.anova_type).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(type_frame, text="Mixed ANOVA", value="mixed", variable=self.anova_type).pack(anchor="w", padx=20, pady=2)
        
        # Factors frame
        factors_frame = ttk.LabelFrame(parent, text="Factors")
        factors_frame.pack(fill="x", padx=10, pady=5)
        
        self.factor_condition = tk.BooleanVar(value=True)
        ttk.Checkbutton(factors_frame, text="Condition", variable=self.factor_condition).pack(anchor="w", padx=20, pady=2)
        
        self.factor_timepoint = tk.BooleanVar(value=True)
        ttk.Checkbutton(factors_frame, text="Timepoint", variable=self.factor_timepoint).pack(anchor="w", padx=20, pady=2)
        
        self.factor_interaction = tk.BooleanVar(value=True)
        ttk.Checkbutton(factors_frame, text="Condition × Timepoint Interaction", variable=self.factor_interaction).pack(anchor="w", padx=20, pady=2)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Run ANOVA", command=self._run_anova).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self._export_anova_results).pack(side="left", padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for ANOVA results
        columns = ("Source", "Sum of Squares", "df", "Mean Square", "F", "p-value", "Partial η²", "Observed Power")
        self.anova_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.anova_tree.heading(col, text=col)
            width = 150 if col == "Source" else 100
            self.anova_tree.column(col, width=width, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.anova_tree.yview)
        self.anova_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.anova_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def _create_posthoc_tab(self, parent):
        """Create post-hoc tests tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Metric Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.posthoc_metric_type = tk.StringVar(value="Global")
        posthoc_metric_combo = ttk.Combobox(selection_frame, textvariable=self.posthoc_metric_type)
        posthoc_metric_combo['values'] = ('Global', 'Nodal', 'Pairwise')
        posthoc_metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Variable:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.posthoc_variable = tk.StringVar()
        self.posthoc_variable_combo = ttk.Combobox(selection_frame, textvariable=self.posthoc_variable)
        self.posthoc_variable_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Update variables when metric type changes
        posthoc_metric_combo.bind("<<ComboboxSelected>>", self._update_posthoc_variables)
        
        # Post-hoc test type frame
        test_frame = ttk.LabelFrame(parent, text="Post-hoc Test")
        test_frame.pack(fill="x", padx=10, pady=5)
        
        self.posthoc_test = tk.StringVar(value="bonferroni")
        ttk.Radiobutton(test_frame, text="Bonferroni", value="bonferroni", variable=self.posthoc_test).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(test_frame, text="Tukey HSD", value="tukey", variable=self.posthoc_test).pack(anchor="w", padx=20, pady=2)
        
        # Factor selection frame
        factor_frame = ttk.LabelFrame(parent, text="Factor")
        factor_frame.pack(fill="x", padx=10, pady=5)
        
        self.posthoc_factor = tk.StringVar(value="condition")
        ttk.Radiobutton(factor_frame, text="Condition", value="condition", variable=self.posthoc_factor).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(factor_frame, text="Timepoint", value="timepoint", variable=self.posthoc_factor).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(factor_frame, text="Condition × Timepoint", value="interaction", variable=self.posthoc_factor).pack(anchor="w", padx=20, pady=2)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Run Post-hoc Test", command=self._run_posthoc_test).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self._export_posthoc_results).pack(side="left", padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for post-hoc results
        columns = ("Group 1", "Group 2", "Mean Diff", "Std Error", "t-value", "p-value", "Significant")
        self.posthoc_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.posthoc_tree.heading(col, text=col)
            self.posthoc_tree.column(col, width=100, anchor="center")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.posthoc_tree.yview)
        self.posthoc_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack elements
        self.posthoc_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
    
    def add_files(self):
        """Open file dialog and add selected files to the list"""
        filetypes = [("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select data files", filetypes=filetypes)
        
        if not files:
            return
            
        for file_path in files:
            # Check if file already exists in the list
            if file_path in [info['path'] for info in self.file_info]:
                continue
                
            # Extract filename and default metadata
            filename = os.path.basename(file_path)
            
            # Try to extract participant ID from filename
            participant_id = self._extract_participant_id(filename)
            
            # Add to file info list
            file_info = {
                'path': file_path,
                'filename': filename,
                'participant_id': participant_id,
                'condition': '',
                'timepoint': '',
                'status': 'Pending'
            }
            
            self.file_info.append(file_info)
            
            # Add to treeview
            item_id = self.file_tree.insert('', 'end', values=(
                filename, participant_id, '', '', 'Pending'
            ))
            
            # Associate the item_id with the file_info
            file_info['item_id'] = item_id
            
        # Prompt user to fill in metadata
        if files:
            messagebox.showinfo("Files Added", f"Added {len(files)} files. Double-click on files to add condition and timepoint information.")
        
    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_items = self.file_tree.selection()
        
        if not selected_items:
            return
            
        # Remove from treeview and file_info list
        for item_id in selected_items:
            # Find the corresponding file_info
            for i, info in enumerate(self.file_info):
                if info.get('item_id') == item_id:
                    del self.file_info[i]
                    break
            
            # Remove from treeview
            self.file_tree.delete(item_id)
    
    def clear_files(self):
        """Clear all files from the list"""
        self.file_info = []
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
    
    def edit_file_metadata(self, event):
        """Show the metadata edit form for the selected file"""
        selected_items = self.file_tree.selection()
        
        if not selected_items:
            return
            
        # Get the selected item (use only the first if multiple selected)
        item_id = selected_items[0]
        
        # Get the corresponding file_info
        selected_info = None
        for info in self.file_info:
            if info.get('item_id') == item_id:
                selected_info = info
                break
                
        if not selected_info:
            return
            
        # Populate the form fields
        self.selected_item_id = item_id
        self.participant_var.set(selected_info['participant_id'])
        self.condition_var.set(selected_info['condition'])
        self.timepoint_var.set(selected_info['timepoint'])
        
        # Show the metadata frame
        self.metadata_frame.pack(fill="x", padx=10, pady=5, after=self.file_tree.master)
    
    def save_metadata(self):
        """Save the metadata for the selected file"""
        if not hasattr(self, 'selected_item_id'):
            return
            
        # Update the file_info
        for info in self.file_info:
            if info.get('item_id') == self.selected_item_id:
                info['participant_id'] = self.participant_var.get()
                info['condition'] = self.condition_var.get()
                info['timepoint'] = self.timepoint_var.get()
                
                # Update the treeview
                self.file_tree.item(self.selected_item_id, values=(
                    info['filename'], 
                    info['participant_id'], 
                    info['condition'], 
                    info['timepoint'], 
                    info['status']
                ))
                
                break
                
        # Hide the metadata frame
        self.metadata_frame.pack_forget()
    
    def load_data(self):
        """Load data for all files with complete metadata"""
        # Check if any files are ready to load
        files_to_load = [info for info in self.file_info 
                        if info['participant_id'] and info['condition'] and info['timepoint']]
        
        if not files_to_load:
            messagebox.showwarning("No Files Ready", "No files have complete metadata. Please add condition and timepoint information.")
            return
        
        # Load each file
        for info in files_to_load:
            try:
                # Prepare metadata for the analysis
                metadata = {
                    'participant_id': info['participant_id'],
                    'condition': info['condition'],
                    'timepoint': info['timepoint']
                }
                
                # Load the data
                self.analyzer.load_data_with_metadata(info['path'], metadata=metadata)
                
                # Update status
                info['status'] = 'Loaded'
                self.file_tree.item(info['item_id'], values=(
                    info['filename'], 
                    info['participant_id'], 
                    info['condition'], 
                    info['timepoint'], 
                    'Loaded'
                ))
                
            except Exception as e:
                info['status'] = 'Error'
                self.file_tree.item(info['item_id'], values=(
                    info['filename'], 
                    info['participant_id'], 
                    info['condition'], 
                    info['timepoint'], 
                    f'Error: {str(e)[:20]}'
                ))
                
                messagebox.showerror("Load Error", f"Error loading file {info['filename']}: {str(e)}")
        
        # Show summary
        loaded_count = sum(1 for info in self.file_info if info['status'] == 'Loaded')
        error_count = sum(1 for info in self.file_info if info['status'].startswith('Error'))
        
        messagebox.showinfo("Load Complete", 
                          f"Loaded {loaded_count} files successfully.\n"
                          f"Errors in {error_count} files.")
    
    def analyze_all(self):
        """Analyze all loaded files"""
        # Check if any files are loaded
        loaded_files = sum(1 for info in self.file_info if info['status'] == 'Loaded')
        
        if loaded_files == 0:
            messagebox.showwarning("No Files Loaded", "No files have been loaded. Please load files first.")
            return
        
        try:
            # Run analysis on all loaded data
            self.analyzer.analyze_all_data()
            
            # Update status
            for info in self.file_info:
                if info['status'] == 'Loaded':
                    info['status'] = 'Analyzed'
                    self.file_tree.item(info['item_id'], values=(
                        info['filename'], 
                        info['participant_id'], 
                        info['condition'], 
                        info['timepoint'], 
                        'Analyzed'
                    ))
            
            messagebox.showinfo("Analysis Complete", f"Successfully analyzed {loaded_files} files.")
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error during analysis: {str(e)}")
    
    def generate_tables(self):
        """Generate and export tables based on the analyzed data"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return
        
        # Ask for grouping type
        groupby_options = ['condition', 'timepoint', 'participant', 'condition_timepoint']
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
            export_dir = filedialog.askdirectory(title="Select directory for table export")
            
            if not export_dir:
                return
            
            # Export tables
            saved_files = self.analyzer.export_tables_to_csv(tables, output_dir=export_dir)
            
            if saved_files:
                messagebox.showinfo("Export Complete", f"Exported {len(saved_files)} tables to {export_dir}")
            else:
                messagebox.showwarning("Export Failed", "No tables were exported.")
                
        except Exception as e:
            messagebox.showerror("Table Generation Error", f"Error generating tables: {str(e)}")
    
    def generate_visualization(self):
        """Generate all types of visualizations (individual, condition, timepoint, condition×timepoint)"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return
        
        # Get selected metric type
        selected_metric_type = self.metric_type.get()
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select directory for visualization output")
        
        if not output_dir:
            return
        
        # Determine which metric types to generate
        metric_types = []
        if selected_metric_type == "All":
            metric_types = ['Global', 'Nodal', 'Network', 'Pairwise', 'Matrix']
        else:
            metric_types = [selected_metric_type]
        
        # Create main figures directory
        figures_dir = os.path.join(output_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        # Create subdirectories for different analysis levels
        individual_dir = os.path.join(figures_dir, 'individual')
        condition_dir = os.path.join(figures_dir, 'condition')
        timepoint_dir = os.path.join(figures_dir, 'timepoint')
        condition_time_dir = os.path.join(figures_dir, 'condition_x_time')
        
        os.makedirs(individual_dir, exist_ok=True)
        os.makedirs(condition_dir, exist_ok=True)
        os.makedirs(timepoint_dir, exist_ok=True)
        os.makedirs(condition_time_dir, exist_ok=True)
        
        try:
            # 1. Individual level: Generate visualizations for each analysis
            for key, analysis in self.analyzer.analyses.items():
                participant_id = analysis['metadata']['participant_id']
                timepoint = analysis['metadata']['timepoint']
                condition = analysis['metadata']['condition']
                
                base_name = f"{participant_id}_{timepoint}_{condition}"
                
                for metric_type in metric_types:
                    self._generate_individual_visualization(analysis, key, metric_type, 
                                                         base_name, individual_dir)
            
            # 2. Condition level: Group by condition (combine timepoints)
            condition_data = {}
            for key, analysis in self.analyzer.analyses.items():
                condition = analysis['metadata']['condition']
                
                if condition not in condition_data:
                    condition_data[condition] = []
                
                condition_data[condition].append((key, analysis))
            
            for condition, analyses in condition_data.items():
                base_name = f"condition_{condition}"
                for metric_type in metric_types:
                    self._generate_group_visualization(analyses, metric_type, 
                                                    base_name, condition_dir, 
                                                    f"Condition: {condition}")
            
            # 3. Timepoint level: Group by timepoint (combine conditions)
            timepoint_data = {}
            for key, analysis in self.analyzer.analyses.items():
                timepoint = analysis['metadata']['timepoint']
                
                if timepoint not in timepoint_data:
                    timepoint_data[timepoint] = []
                
                timepoint_data[timepoint].append((key, analysis))
            
            for timepoint, analyses in timepoint_data.items():
                base_name = f"timepoint_{timepoint}"
                for metric_type in metric_types:
                    self._generate_group_visualization(analyses, metric_type, 
                                                    base_name, timepoint_dir, 
                                                    f"Timepoint: {timepoint}")
            
            # 4. Condition x Timepoint level: Create time-series visualization
            # First, organize data by condition and timepoint
            condition_timepoint_data = {}
            
            # Get all conditions and timepoints
            all_conditions = set()
            all_timepoints = set()
            
            for key, analysis in self.analyzer.analyses.items():
                condition = analysis['metadata']['condition']
                timepoint = analysis['metadata']['timepoint']
                
                all_conditions.add(condition)
                all_timepoints.add(timepoint)
                
                if condition not in condition_timepoint_data:
                    condition_timepoint_data[condition] = {}
                
                condition_timepoint_data[condition][timepoint] = (key, analysis)
            
            # Convert to sorted lists
            all_conditions = sorted(all_conditions)
            all_timepoints = sorted(all_timepoints)
            
            # Generate time-series visualization for each metric type
            for metric_type in metric_types:
                self._generate_time_series_visualization(condition_timepoint_data, 
                                                      all_conditions, all_timepoints, 
                                                      metric_type, condition_time_dir)
            
            messagebox.showinfo("Visualization Complete", 
                             f"All visualizations have been generated for the following levels:\n\n"
                             f"- Individual participants ({len(self.analyzer.analyses)} analyses)\n"
                             f"- By condition ({len(condition_data)} conditions)\n"
                             f"- By timepoint ({len(timepoint_data)} timepoints)\n"
                             f"- Condition × Timepoint interactions")
            
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Visualization Error", f"Error generating visualization: {str(e)}")

    def _generate_individual_visualization(self, analysis, key, metric_type, base_name, output_dir):
        """Generate individual visualization for a single analysis"""
        participant_id = analysis['metadata']['participant_id']
        timepoint = analysis['metadata']['timepoint']
        condition = analysis['metadata']['condition']
        
        title = f"{metric_type} Metrics: {participant_id} {timepoint} {condition}"
        
        if metric_type == "Global":
            plot_global_metrics(
                analysis['global'], 
                title, 
                os.path.join(output_dir, f"{base_name}_global.png")
            )
        
        elif metric_type == "Nodal":
            plot_nodal_metrics(
                analysis['nodal'], 
                title, 
                os.path.join(output_dir, f"{base_name}_nodal.png")
            )
        
        elif metric_type == "Network":
            G = self.analyzer.create_network_graph(key)
            plot_network_graph(
                G, 
                title, 
                os.path.join(output_dir, f"{base_name}_network.png")
            )
        
        elif metric_type == "Pairwise":
            plot_pairwise_comparison(
                analysis['pairwise'], 
                title, 
                os.path.join(output_dir, f"{base_name}_pairwise.png")
            )
        
        elif metric_type == "Matrix":
            plot_connectivity_matrix(
                analysis['connectivity_matrix'], 
                title, 
                os.path.join(output_dir, f"{base_name}_matrix.png")
            )

    def _generate_group_visualization(self, analyses, metric_type, base_name, output_dir, title_prefix):
        """Generate group-level visualization by combining multiple analyses"""
        if metric_type == "Global":
            # Combine global metrics across analyses
            combined_global = self._combine_global_metrics([a for _, a in analyses])
            plot_global_metrics(
                combined_global, 
                f"{title_prefix} - Global Metrics", 
                os.path.join(output_dir, f"{base_name}_global.png")
            )
        
        elif metric_type == "Nodal":
            # Combine nodal metrics across analyses
            combined_nodal = self._combine_nodal_metrics([a for _, a in analyses])
            plot_nodal_metrics(
                combined_nodal, 
                f"{title_prefix} - Nodal Metrics", 
                os.path.join(output_dir, f"{base_name}_nodal.png")
            )
        
        elif metric_type == "Network":
            # Create an average connectivity matrix and convert to graph
            combined_matrix = self._combine_connectivity_matrices([a for _, a in analyses])
            
            # Convert to graph
            G = nx.DiGraph()
            for source in combined_matrix.index:
                for target in combined_matrix.columns:
                    if source != target and combined_matrix.loc[source, target] > 0.0005:
                        G.add_edge(source, target, weight=combined_matrix.loc[source, target])
            
            plot_network_graph(
                G, 
                f"{title_prefix} - Network Graph", 
                os.path.join(output_dir, f"{base_name}_network.png")
            )
        
        elif metric_type == "Pairwise":
            # Combine pairwise metrics across analyses
            combined_pairwise = self._combine_pairwise_metrics([a for _, a in analyses])
            plot_pairwise_comparison(
                combined_pairwise, 
                f"{title_prefix} - Pairwise Connections", 
                os.path.join(output_dir, f"{base_name}_pairwise.png")
            )
        
        elif metric_type == "Matrix":
            # Create an average connectivity matrix
            combined_matrix = self._combine_connectivity_matrices([a for _, a in analyses])
            plot_connectivity_matrix(
                combined_matrix, 
                f"{title_prefix} - Connectivity Matrix", 
                os.path.join(output_dir, f"{base_name}_matrix.png")
            )

    def _generate_time_series_visualization(self, condition_timepoint_data, all_conditions, all_timepoints, metric_type, output_dir):
        """Generate visualizations showing how conditions change over time"""
        all_timepoints = sorted(all_timepoints)
        
        # Create a subdirectory specifically for time series plots
        timeseries_dir = os.path.join(output_dir, "condition_x_time")
        os.makedirs(timeseries_dir, exist_ok=True)
        
        if metric_type == "Global":
            # For each global metric, create a figure showing changes over time
            # Get the first analysis to see what metrics are available
            first_condition = next(iter(condition_timepoint_data))
            first_timepoint = next(iter(condition_timepoint_data[first_condition]))
            first_analysis = condition_timepoint_data[first_condition][first_timepoint][1]
            
            for metric_name in first_analysis['global'].keys():
                # Create a figure for this metric
                plt.figure(figsize=(12, 8))
                
                # Extract data for each condition across timepoints
                for condition in all_conditions:
                    if condition in condition_timepoint_data:
                        timepoints = []
                        values = []
                        
                        for timepoint in all_timepoints:
                            if timepoint in condition_timepoint_data[condition]:
                                analysis = condition_timepoint_data[condition][timepoint][1]
                                if metric_name in analysis['global']:
                                    timepoints.append(timepoint)
                                    values.append(analysis['global'][metric_name])
                        
                        if timepoints and values:
                            plt.plot(timepoints, values, 'o-', linewidth=2, markersize=8, label=condition)
                
                plt.title(f"Changes in {metric_name} Over Time", fontsize=16)
                plt.xlabel("Timepoint", fontsize=14)
                plt.ylabel(metric_name, fontsize=14)
                plt.legend(fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # Save the figure
                plt.savefig(os.path.join(timeseries_dir, f"timeseries_{metric_name}.png"), dpi=300, bbox_inches='tight')
                plt.close()
                
                # Additionally, create a heatmap for condition x timepoint
                data = {}
                for condition in all_conditions:
                    if condition in condition_timepoint_data:
                        condition_values = []
                        for timepoint in all_timepoints:
                            if timepoint in condition_timepoint_data[condition]:
                                analysis = condition_timepoint_data[condition][timepoint][1]
                                if metric_name in analysis['global']:
                                    condition_values.append(analysis['global'][metric_name])
                            else:
                                condition_values.append(float('nan'))  # Use NaN for missing data
                        data[condition] = condition_values
                
                if data:
                    heatmap_df = pd.DataFrame(data, index=all_timepoints)
                    plt.figure(figsize=(10, 8))
                    sns.heatmap(heatmap_df, annot=True, cmap="YlGnBu", linewidths=.5, fmt=".3f")
                    plt.title(f"Heatmap of {metric_name} (Condition × Timepoint)", fontsize=16)
                    plt.tight_layout()
                    plt.savefig(os.path.join(timeseries_dir, f"heatmap_{metric_name}.png"), dpi=300, bbox_inches='tight')
                    plt.close()
        
        elif metric_type == "Nodal":
            # For each electrode, create figures showing in-strength, out-strength, and causal flow over time
            all_electrodes = set()
            
            # Get all electrodes from all analyses
            for condition in condition_timepoint_data:
                for timepoint in condition_timepoint_data[condition]:
                    analysis = condition_timepoint_data[condition][timepoint][1]
                    all_electrodes.update(analysis['nodal'].keys())
            
            for electrode in sorted(all_electrodes):
                # Create a separate directory for each electrode
                electrode_dir = os.path.join(timeseries_dir, f"electrode_{electrode}")
                os.makedirs(electrode_dir, exist_ok=True)
                
                for metric_name in ['in_strength', 'out_strength', 'causal_flow']:
                    # Create a figure for this electrode and metric
                    plt.figure(figsize=(12, 8))
                    
                    # Extract data for each condition across timepoints
                    for condition in all_conditions:
                        if condition in condition_timepoint_data:
                            timepoints = []
                            values = []
                            
                            for timepoint in all_timepoints:
                                if timepoint in condition_timepoint_data[condition]:
                                    analysis = condition_timepoint_data[condition][timepoint][1]
                                    if electrode in analysis['nodal'] and metric_name in analysis['nodal'][electrode]:
                                        timepoints.append(timepoint)
                                        values.append(analysis['nodal'][electrode][metric_name])
                            
                            if timepoints and values:
                                plt.plot(timepoints, values, 'o-', linewidth=2, markersize=8, label=condition)
                    
                    plt.title(f"Changes in {electrode} {metric_name} Over Time", fontsize=16)
                    plt.xlabel("Timepoint", fontsize=14)
                    plt.ylabel(metric_name, fontsize=14)
                    plt.legend(fontsize=12)
                    plt.grid(True, linestyle='--', alpha=0.7)
                    
                    # Save the figure
                    plt.savefig(os.path.join(electrode_dir, f"{electrode}_{metric_name}.png"), dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    # Create a heatmap for condition x timepoint
                    data = {}
                    for condition in all_conditions:
                        if condition in condition_timepoint_data:
                            condition_values = []
                            for timepoint in all_timepoints:
                                if timepoint in condition_timepoint_data[condition] and electrode in condition_timepoint_data[condition][timepoint][1]['nodal']:
                                    analysis = condition_timepoint_data[condition][timepoint][1]
                                    if metric_name in analysis['nodal'][electrode]:
                                        condition_values.append(analysis['nodal'][electrode][metric_name])
                                else:
                                    condition_values.append(float('nan'))  # Use NaN for missing data
                            data[condition] = condition_values
                    
                    if data:
                        heatmap_df = pd.DataFrame(data, index=all_timepoints)
                        plt.figure(figsize=(10, 8))
                        sns.heatmap(heatmap_df, annot=True, cmap="YlGnBu", linewidths=.5, fmt=".3f")
                        plt.title(f"Heatmap of {electrode} {metric_name} (Condition × Timepoint)", fontsize=16)
                        plt.tight_layout()
                        plt.savefig(os.path.join(electrode_dir, f"heatmap_{electrode}_{metric_name}.png"), dpi=300, bbox_inches='tight')
                        plt.close()
                
                # Create a composite figure showing all three metrics for this electrode
                fig, axes = plt.subplots(3, 1, figsize=(12, 18), sharex=True)
                metric_names = ['in_strength', 'out_strength', 'causal_flow']
                
                for i, metric_name in enumerate(metric_names):
                    ax = axes[i]
                    for condition in all_conditions:
                        if condition in condition_timepoint_data:
                            timepoints = []
                            values = []
                            
                            for timepoint in all_timepoints:
                                if timepoint in condition_timepoint_data[condition]:
                                    analysis = condition_timepoint_data[condition][timepoint][1]
                                    if electrode in analysis['nodal'] and metric_name in analysis['nodal'][electrode]:
                                        timepoints.append(timepoint)
                                        values.append(analysis['nodal'][electrode][metric_name])
                            
                            if timepoints and values:
                                ax.plot(timepoints, values, 'o-', linewidth=2, markersize=8, label=condition)
                    
                    ax.set_title(f"{electrode} {metric_name}", fontsize=14)
                    ax.set_ylabel(metric_name, fontsize=12)
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    if i == 0:
                        ax.legend(fontsize=12)
                
                axes[-1].set_xlabel("Timepoint", fontsize=14)
                fig.suptitle(f"All Metrics for Electrode {electrode}", fontsize=18)
                plt.tight_layout(rect=[0, 0, 1, 0.97])
                plt.savefig(os.path.join(electrode_dir, f"{electrode}_all_metrics.png"), dpi=300, bbox_inches='tight')
                plt.close()
        
        elif metric_type in ["Network", "Matrix"]:
            # For network and matrix, we'll create a grid of visualizations for each condition at each timepoint
            for condition in all_conditions:
                if condition in condition_timepoint_data:
                    # Create a condition directory
                    condition_dir = os.path.join(timeseries_dir, f"condition_{condition}")
                    os.makedirs(condition_dir, exist_ok=True)
                    
                    for timepoint in all_timepoints:
                        if timepoint in condition_timepoint_data[condition]:
                            key, analysis = condition_timepoint_data[condition][timepoint]
                            title = f"{condition}, {timepoint}"
                            base_name = f"condition_{condition}_timepoint_{timepoint}"
                            
                            if metric_type == "Network":
                                G = self.analyzer.create_network_graph(key)
                                plot_network_graph(
                                    G, 
                                    title, 
                                    os.path.join(condition_dir, f"{base_name}_network.png")
                                )
                            
                            elif metric_type == "Matrix":
                                plot_connectivity_matrix(
                                    analysis['connectivity_matrix'], 
                                    title, 
                                    os.path.join(condition_dir, f"{base_name}_matrix.png")
                                )
            
            # Also create a visual comparison grid
            if metric_type == "Matrix":
                # Create a multi-panel figure showing all matrices
                n_conditions = len(all_conditions)
                n_timepoints = len(all_timepoints)
                
                # Determine grid dimensions
                grid_size = (n_conditions, n_timepoints)
                
                # Create the figure
                if n_conditions > 0 and n_timepoints > 0:
                    fig, axes = plt.subplots(n_conditions, n_timepoints, 
                                            figsize=(n_timepoints*4, n_conditions*4),
                                            squeeze=False)
                    
                    # Plot each matrix
                    for i, condition in enumerate(sorted(all_conditions)):
                        for j, timepoint in enumerate(sorted(all_timepoints)):
                            ax = axes[i, j]
                            
                            if condition in condition_timepoint_data and timepoint in condition_timepoint_data[condition]:
                                key, analysis = condition_timepoint_data[condition][timepoint]
                                matrix = analysis['connectivity_matrix']
                                
                                # Plot the matrix as a heatmap
                                sns.heatmap(matrix, ax=ax, cmap="YlGnBu", vmin=0, 
                                          cbar=True if j == n_timepoints-1 else False)
                                
                                ax.set_title(f"{condition}, {timepoint}")
                            else:
                                ax.set_visible(False)
                    
                    plt.tight_layout()
                    plt.savefig(os.path.join(timeseries_dir, "matrix_grid_comparison.png"), dpi=300, bbox_inches='tight')
                    plt.close()
        
        elif metric_type == "Pairwise":
            # For pairwise, we'll focus on top connections and how they change over time
            # First, identify top connections across all analyses
            all_pairs = set()
            pair_values = {}
            
            for condition in condition_timepoint_data:
                for timepoint in condition_timepoint_data[condition]:
                    analysis = condition_timepoint_data[condition][timepoint][1]
                    for pair, value in analysis['pairwise']['directional_pairs'].items():
                        all_pairs.add(pair)
                        if pair not in pair_values:
                            pair_values[pair] = []
                        pair_values[pair].append(value)
            
            # Sort pairs by average value and select top 15
            top_pairs = sorted(all_pairs, key=lambda p: np.mean(pair_values.get(p, [0])), reverse=True)[:15]
            
            # Create a directory for pairwise plots
            pairwise_dir = os.path.join(timeseries_dir, "pairwise")
            os.makedirs(pairwise_dir, exist_ok=True)
            
            for pair in top_pairs:
                # Create a figure for this pair
                plt.figure(figsize=(12, 8))
                
                # Extract data for each condition across timepoints
                for condition in all_conditions:
                    if condition in condition_timepoint_data:
                        timepoints = []
                        values = []
                        
                        for timepoint in all_timepoints:
                            if timepoint in condition_timepoint_data[condition]:
                                analysis = condition_timepoint_data[condition][timepoint][1]
                                if pair in analysis['pairwise']['directional_pairs']:
                                    timepoints.append(timepoint)
                                    values.append(analysis['pairwise']['directional_pairs'][pair])
                        
                        if timepoints and values:
                            plt.plot(timepoints, values, 'o-', linewidth=2, markersize=8, label=condition)
                
                plt.title(f"Changes in Connection {pair} Over Time", fontsize=16)
                plt.xlabel("Timepoint", fontsize=14)
                plt.ylabel("Granger Causality Value", fontsize=14)
                plt.legend(fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # Save the figure
                plt.savefig(os.path.join(pairwise_dir, f"{pair.replace('→','_to_')}.png"), dpi=300, bbox_inches='tight')
                plt.close()
            
            # Create a heatmap of top pairs across conditions and timepoints
            for condition in all_conditions:
                if condition in condition_timepoint_data:
                    # Create a matrix of timepoints x pairs
                    data = []
                    for timepoint in all_timepoints:
                        if timepoint in condition_timepoint_data[condition]:
                            row = {}
                            analysis = condition_timepoint_data[condition][timepoint][1]
                            for pair in top_pairs:
                                if pair in analysis['pairwise']['directional_pairs']:
                                    row[pair] = analysis['pairwise']['directional_pairs'][pair]
                                else:
                                    row[pair] = 0
                            data.append(row)
                        else:
                            row = {pair: 0 for pair in top_pairs}
                            data.append(row)
                    
                    if data:
                        df = pd.DataFrame(data, index=all_timepoints)
                        plt.figure(figsize=(16, 10))
                        sns.heatmap(df, annot=True, cmap="YlGnBu", linewidths=.5, fmt=".3f")
                        plt.title(f"Top GC Connections for Condition: {condition}", fontsize=16)
                        plt.tick_params(axis='x', rotation=45)
                        plt.tight_layout()
                        plt.savefig(os.path.join(pairwise_dir, f"heatmap_{condition}.png"), dpi=300, bbox_inches='tight')
                        plt.close()
            
            # Create a composite figure with all top pairs for each condition
            for condition in all_conditions:
                if condition in condition_timepoint_data:
                    n_pairs = min(len(top_pairs), 6)  # Show top 6 pairs at most
                    if n_pairs > 0:
                        n_rows = (n_pairs + 1) // 2  # 2 columns per row
                        fig, axes = plt.subplots(n_rows, 2, figsize=(16, n_rows*5), squeeze=False)
                        
                        for i, pair in enumerate(top_pairs[:n_pairs]):
                            row, col = i // 2, i % 2
                            ax = axes[row, col]
                            
                            timepoints = []
                            values = []
                            
                            for timepoint in all_timepoints:
                                if timepoint in condition_timepoint_data[condition]:
                                    analysis = condition_timepoint_data[condition][timepoint][1]
                                    if pair in analysis['pairwise']['directional_pairs']:
                                        timepoints.append(timepoint)
                                        values.append(analysis['pairwise']['directional_pairs'][pair])
                            
                            if timepoints and values:
                                ax.plot(timepoints, values, 'o-', linewidth=2, markersize=8, color='blue')
                                ax.set_title(f"Connection: {pair}", fontsize=14)
                                ax.set_xlabel("Timepoint", fontsize=12)
                                ax.set_ylabel("GC Value", fontsize=12)
                                ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # Hide any unused subplots
                        for i in range(n_pairs, n_rows*2):
                            row, col = i // 2, i % 2
                            axes[row, col].set_visible(False)
                            
                        plt.tight_layout()
                        plt.savefig(os.path.join(pairwise_dir, f"top_pairs_{condition}.png"), dpi=300, bbox_inches='tight')
                        plt.close()

    def _combine_global_metrics(self, analyses):
        """Combine global metrics from multiple analyses"""
        combined = {}
        
        # Get all metric names
        metric_names = set()
        for analysis in analyses:
            metric_names.update(analysis['global'].keys())
        
        # Compute mean for each metric
        for metric in metric_names:
            values = [analysis['global'][metric] for analysis in analyses if metric in analysis['global']]
            if values:
                combined[metric] = sum(values) / len(values)
        
        return combined

    def _combine_nodal_metrics(self, analyses):
        """Combine nodal metrics from multiple analyses"""
        combined = {}
        
        # Get all electrodes
        all_electrodes = set()
        for analysis in analyses:
            all_electrodes.update(analysis['nodal'].keys())
        
        # Compute mean metrics for each electrode
        for electrode in all_electrodes:
            combined[electrode] = {}
            
            # Get all analyses that have this electrode
            electrode_analyses = [a for a in analyses if electrode in a['nodal']]
            
            if electrode_analyses:
                # Get the metric names from the first analysis
                metric_names = [m for m in electrode_analyses[0]['nodal'][electrode].keys() if m != 'category']
                
                for metric in metric_names:
                    values = [a['nodal'][electrode][metric] for a in electrode_analyses if metric in a['nodal'][electrode]]
                    if values:
                        combined[electrode][metric] = sum(values) / len(values)
                
                # Determine dominant category
                categories = [a['nodal'][electrode]['category'] for a in electrode_analyses if 'category' in a['nodal'][electrode]]
                if categories:
                    combined[electrode]['category'] = max(set(categories), key=categories.count)
        
        return combined

    def _combine_pairwise_metrics(self, analyses):
        """Combine pairwise metrics from multiple analyses"""
        combined_pairs = {}
        
        # Get all pairs
        all_pairs = set()
        for analysis in analyses:
            all_pairs.update(analysis['pairwise']['directional_pairs'].keys())
        
        # Compute mean for each pair
        for pair in all_pairs:
            values = [analysis['pairwise']['directional_pairs'][pair] 
                     for analysis in analyses 
                     if pair in analysis['pairwise']['directional_pairs']]
            
            if values:
                combined_pairs[pair] = sum(values) / len(values)
        
        return {'directional_pairs': combined_pairs}

    def _combine_connectivity_matrices(self, analyses):
        """Combine connectivity matrices from multiple analyses"""
        # Get all electrodes
        all_electrodes = set()
        for analysis in analyses:
            matrix = analysis['connectivity_matrix']
            all_electrodes.update(matrix.index)
        
        all_electrodes = sorted(all_electrodes)
        
        # Create an empty matrix with all electrodes
        combined_matrix = pd.DataFrame(0, index=all_electrodes, columns=all_electrodes)
        
        # Fill the matrix by averaging values
        for source in all_electrodes:
            for target in all_electrodes:
                values = []
                
                for analysis in analyses:
                    matrix = analysis['connectivity_matrix']
                    if source in matrix.index and target in matrix.columns:
                        values.append(matrix.loc[source, target])
                
                if values:
                    combined_matrix.loc[source, target] = sum(values) / len(values)
        
        return combined_matrix
    
    def export_visualizations(self):
        """Export visualizations to files"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return
            
        # Ask for export directory
        export_dir = filedialog.askdirectory(title="Select directory for visualization export")
        
        if not export_dir:
            return
            
        # Create figures directory if it doesn't exist
        figures_dir = os.path.join(export_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        # Track how many of each type we exported
        exported_counts = {
            'matrix': 0,
            'network': 0,
            'nodal': 0,
            'pairwise': 0,
            'global': 0
        }
        
        # Generate visualizations for each analysis
        for key, analysis in self.analyzer.analyses.items():
            participant_id = analysis['metadata']['participant_id']
            timepoint = analysis['metadata']['timepoint']
            condition = analysis['metadata']['condition']
            
            base_name = f"{participant_id}_{timepoint}_{condition}"
            print(f"Exporting visualizations for: {base_name}")
            
            # Generate matrix visualization
            plot_connectivity_matrix(
                analysis['connectivity_matrix'], 
                f"Granger Causality Matrix: {participant_id} {timepoint} {condition}", 
                os.path.join(figures_dir, f"{base_name}_matrix.png")
            )
            exported_counts['matrix'] += 1
            
            # Generate network visualization
            G = self.analyzer.create_network_graph(key)
            plot_network_graph(
                G, 
                f"Granger Causality Network: {participant_id} {timepoint} {condition}", 
                os.path.join(figures_dir, f"{base_name}_network.png")
            )
            exported_counts['network'] += 1
            
            # Generate nodal metrics visualization
            plot_nodal_metrics(
                analysis['nodal'], 
                f"Nodal Metrics: {participant_id} {timepoint} {condition}", 
                os.path.join(figures_dir, f"{base_name}_nodal.png")
            )
            exported_counts['nodal'] += 1
            
            # Generate pairwise comparison visualization
            plot_pairwise_comparison(
                analysis['pairwise'], 
                f"Pairwise Connections: {participant_id} {timepoint} {condition}", 
                os.path.join(figures_dir, f"{base_name}_pairwise.png")
            )
            exported_counts['pairwise'] += 1
            
            # Generate global metrics visualization
            plot_global_metrics(
                analysis['global'], 
                f"Global Metrics: {participant_id} {timepoint} {condition}", 
                os.path.join(figures_dir, f"{base_name}_global.png")
            )
            exported_counts['global'] += 1
        
        # Show summary message
        total_exported = sum(exported_counts.values())
        messagebox.showinfo(
            "Export Complete", 
            f"Successfully exported {total_exported} visualizations to {figures_dir}:\n"
            f"- {exported_counts['matrix']} matrix visualizations\n"
            f"- {exported_counts['network']} network visualizations\n"
            f"- {exported_counts['nodal']} nodal metrics visualizations\n"
            f"- {exported_counts['pairwise']} pairwise connections visualizations\n"
            f"- {exported_counts['global']} global metrics visualizations"
        )
    
    def _extract_participant_id(self, filename):
        """Try to extract participant ID from filename"""
        # This is a simple example - adjust based on your filename conventions
        parts = filename.split('_')
        if parts and len(parts) > 0:
            # If filename looks like "sub-001_task.csv" or similar
            if parts[0].startswith('sub-'):
                return parts[0]
            # Just use the first part as a guess
            return parts[0]
        return ""
    
    def _ask_groupby(self):
        """Ask user for groupby option"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Group By")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select grouping option:").pack(pady=10)
        
        groupby_var = tk.StringVar()
        
        ttk.Radiobutton(dialog, text="By Condition", value="condition", variable=groupby_var).pack(anchor="w", padx=20)
        ttk.Radiobutton(dialog, text="By Timepoint", value="timepoint", variable=groupby_var).pack(anchor="w", padx=20)
        ttk.Radiobutton(dialog, text="By Participant", value="participant", variable=groupby_var).pack(anchor="w", padx=20)
        ttk.Radiobutton(dialog, text="By Condition × Timepoint", value="condition_timepoint", variable=groupby_var).pack(anchor="w", padx=20)
        
        result = [None]  # To store the result
        
        def on_ok():
            result[0] = groupby_var.get()
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
            
        ttk.Button(dialog, text="OK", command=on_ok).pack(side="right", padx=10, pady=10)
        ttk.Button(dialog, text="Cancel", command=on_cancel).pack(side="right", padx=10, pady=10)
        
        # Wait for dialog to be closed
        self.root.wait_window(dialog)
        
        return result[0]

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Files", command=self.add_files)
        file_menu.add_command(label="Clear All", command=self.clear_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Load Data", command=self.load_data)
        analysis_menu.add_command(label="Analyze All", command=self.analyze_all)
        analysis_menu.add_command(label="Generate Tables", command=self.generate_tables)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # Visualization menu
        viz_menu = tk.Menu(menubar, tearoff=0)
        viz_menu.add_command(label="Generate Visualization", command=self.generate_visualization)
        viz_menu.add_command(label="Export Visualizations", command=self.export_visualizations)
        menubar.add_cascade(label="Visualization", menu=viz_menu)
        
        # Statistics menu
        stats_menu = tk.Menu(menubar, tearoff=0)
        stats_menu.add_command(label="Open Statistics Window", command=self.create_stats_frame)
        menubar.add_cascade(label="Statistics", menu=stats_menu)
        
        # Set the menu
        self.root.config(menu=menubar)

    def _update_outlier_variables(self, event=None):
        """Update the variable dropdown based on the selected metric type"""
        metric_type = self.outlier_metric_type.get()
        
        # Clear the current variable list
        self.outlier_variable_combo['values'] = []
        self.outlier_variable.set('')
        
        # Check if we have any analyses
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return
        
        # Get the first analysis to check available metrics
        first_analysis = next(iter(self.analyzer.analyses.values()))
        
        if metric_type == 'Global':
            # Get global metrics from the first analysis
            variables = list(first_analysis['global'].keys())
            self.outlier_variable_combo['values'] = variables
            if variables:
                self.outlier_variable.set(variables[0])
        
        elif metric_type == 'Nodal':
            # Get nodal metrics keys from the first electrode
            if first_analysis['nodal']:
                first_electrode = next(iter(first_analysis['nodal'].keys()))
                variables = [f"{key}" for key in first_analysis['nodal'][first_electrode].keys() 
                           if key != 'category']  # Exclude categorical values
                self.outlier_variable_combo['values'] = variables
                if variables:
                    self.outlier_variable.set(variables[0])
        
        elif metric_type == 'Pairwise':
            # For pairwise we only have GC values
            self.outlier_variable_combo['values'] = ['GC Value']
            self.outlier_variable.set('GC Value')
    
    def _update_normality_variables(self, event=None):
        """Update the variable dropdown for normality tests"""
        # Reuse the outlier variables update function as it's the same logic
        self._update_outlier_variables(event)
        self.normality_variable.set(self.outlier_variable.get())
        self.normality_variable_combo['values'] = self.outlier_variable_combo['values']
    
    def _update_assumption_variables(self, event=None):
        """Update the variable dropdown for assumption tests"""
        # Reuse the outlier variables update function as it's the same logic
        self._update_outlier_variables(event)
        self.assumption_variable.set(self.outlier_variable.get())
        self.assumption_variable_combo['values'] = self.outlier_variable_combo['values']
    
    def _update_anova_variables(self, event=None):
        """Update the variable dropdown for ANOVA"""
        # Reuse the outlier variables update function as it's the same logic
        self._update_outlier_variables(event)
        self.anova_variable.set(self.outlier_variable.get())
        self.anova_variable_combo['values'] = self.outlier_variable_combo['values']
    
    def _update_posthoc_variables(self, event=None):
        """Update the variable dropdown for post-hoc tests"""
        # Reuse the outlier variables update function as it's the same logic
        self._update_outlier_variables(event)
        self.posthoc_variable.set(self.outlier_variable.get())
        self.posthoc_variable_combo['values'] = self.outlier_variable_combo['values']
    
    def _extract_data_for_analysis(self, metric_type, variable):
        """Extract data for statistical analysis based on metric type and variable"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return None
        
        data = []
        
        for key, analysis in self.analyzer.analyses.items():
            participant_id = analysis['metadata']['participant_id']
            timepoint = analysis['metadata']['timepoint']
            condition = analysis['metadata']['condition']
            
            if metric_type == 'Global':
                if variable in analysis['global']:
                    data.append({
                        'Participant': participant_id,
                        'Condition': condition,
                        'Timepoint': timepoint,
                        'Value': analysis['global'][variable]
                    })
            
            elif metric_type == 'Nodal':
                for electrode, metrics in analysis['nodal'].items():
                    if variable in metrics and variable != 'category':
                        data.append({
                            'Participant': participant_id,
                            'Condition': condition,
                            'Timepoint': timepoint,
                            'Electrode': electrode,
                            'Value': metrics[variable]
                        })
            
            elif metric_type == 'Pairwise':
                for pair, value in analysis['pairwise']['directional_pairs'].items():
                    source, target = pair.split('→')
                    data.append({
                        'Participant': participant_id,
                        'Condition': condition,
                        'Timepoint': timepoint,
                        'Source': source,
                        'Target': target,
                        'Pair': pair,
                        'Value': value
                    })
        
        if not data:
            messagebox.showwarning("No Data", f"No data available for {metric_type} metric: {variable}")
            return None
        
        return pd.DataFrame(data)
    
    def _detect_outliers(self):
        """Detect outliers in the selected variable"""
        # Get selected variable and method
        metric_type = self.outlier_metric_type.get()
        variable = self.outlier_variable.get()
        method = self.outlier_method.get()
        
        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return
        
        # Extract data
        df = self._extract_data_for_analysis(metric_type, variable)
        
        if df is None:
            return
        
        # Clear the treeview
        for item in self.outlier_tree.get_children():
            self.outlier_tree.delete(item)
        
        # Detect outliers
        if method == 'z_score':
            # Using Z-Score method (±3 standard deviations)
            mean = df['Value'].mean()
            std = df['Value'].std()
            threshold = 3
            
            for _, row in df.iterrows():
                z_score = abs((row['Value'] - mean) / std) if std > 0 else 0
                is_outlier = z_score > threshold
                
                values = [row.get(col, '') for col in ['Participant', 'Condition', 'Timepoint']]
                values.append(row['Value'])
                values.append("Outlier" if is_outlier else "Normal")
                
                item_id = self.outlier_tree.insert('', 'end', values=values)
                
                if is_outlier:
                    self.outlier_tree.item(item_id, tags=('outlier',))
            
            # Configure the tag
            self.outlier_tree.tag_configure('outlier', background='#ffcccc')
            
            # Show the outlier count
            outlier_count = sum(1 for _, row in df.iterrows() if abs((row['Value'] - mean) / std if std > 0 else 0) > threshold)
            messagebox.showinfo("Outlier Detection", f"Detected {outlier_count} outliers using Z-Score method (±{threshold} SD)")
        
        elif method == 'iqr':
            # Using IQR method (1.5 × IQR)
            q1 = df['Value'].quantile(0.25)
            q3 = df['Value'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for _, row in df.iterrows():
                is_outlier = row['Value'] < lower_bound or row['Value'] > upper_bound
                
                values = [row.get(col, '') for col in ['Participant', 'Condition', 'Timepoint']]
                values.append(row['Value'])
                values.append("Outlier" if is_outlier else "Normal")
                
                item_id = self.outlier_tree.insert('', 'end', values=values)
                
                if is_outlier:
                    self.outlier_tree.item(item_id, tags=('outlier',))
            
            # Configure the tag
            self.outlier_tree.tag_configure('outlier', background='#ffcccc')
            
            # Show the outlier count
            outlier_count = sum(1 for _, row in df.iterrows() if row['Value'] < lower_bound or row['Value'] > upper_bound)
            messagebox.showinfo("Outlier Detection", f"Detected {outlier_count} outliers using IQR method (1.5 × IQR)")
    
    def _remove_outliers(self):
        """Remove outliers from the dataset"""
        # Get selected outliers
        selected_items = self.outlier_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select outliers to remove")
            return
        
        # Confirm removal
        confirmed = messagebox.askyesno("Confirm Removal", "Are you sure you want to remove the selected outliers? This will modify the analysis results.")
        
        if not confirmed:
            return
        
        # Get current metric type and variable
        metric_type = self.outlier_metric_type.get()
        variable = self.outlier_variable.get()
        
        # Get the participant, condition, timepoint information for the selected outliers
        outliers_to_remove = []
        for item_id in selected_items:
            values = self.outlier_tree.item(item_id, 'values')
            # Get the first three columns: Participant, Condition, Timepoint
            participant = values[0]
            condition = values[1]
            timepoint = values[2]
            value = values[3]
            
            if participant and condition and timepoint:
                outliers_to_remove.append((participant, condition, timepoint))
        
        # Remove the outliers from the analyses
        removed_count = 0
        
        for key, analysis in list(self.analyzer.analyses.items()):
            participant_id = analysis['metadata']['participant_id']
            condition = analysis['metadata']['condition']
            timepoint = analysis['metadata']['timepoint']
            
            # Check if this analysis is in the list of outliers to remove
            if (participant_id, condition, timepoint) in outliers_to_remove:
                # Handle different metric types
                if metric_type == 'Global':
                    # For global metrics, we need to replace the outlier value with the mean
                    # First, collect all non-outlier values for this metric
                    all_values = []
                    for _, other_analysis in self.analyzer.analyses.items():
                        if variable in other_analysis['global'] and (other_analysis['metadata']['participant_id'], 
                                other_analysis['metadata']['condition'], 
                                other_analysis['metadata']['timepoint']) not in outliers_to_remove:
                            all_values.append(other_analysis['global'][variable])
                    
                    # Calculate mean if we have enough values
                    if all_values:
                        mean_value = sum(all_values) / len(all_values)
                        # Replace outlier value with mean
                        self.analyzer.analyses[key]['global'][variable] = mean_value
                        removed_count += 1
                
                elif metric_type == 'Nodal':
                    # For nodal metrics, we need to find the specific electrode
                    # This is more complex, as we need electrode information
                    # For simplicity, we'll just set it to the mean of other participants
                    for electrode in analysis['nodal']:
                        if variable in analysis['nodal'][electrode]:
                            # Collect all non-outlier values for this electrode and metric
                            all_values = []
                            for _, other_analysis in self.analyzer.analyses.items():
                                if (other_analysis['metadata']['participant_id'], 
                                        other_analysis['metadata']['condition'], 
                                        other_analysis['metadata']['timepoint']) not in outliers_to_remove:
                                    if electrode in other_analysis['nodal'] and variable in other_analysis['nodal'][electrode]:
                                        all_values.append(other_analysis['nodal'][electrode][variable])
                            
                            # Calculate mean if we have enough values
                            if all_values:
                                mean_value = sum(all_values) / len(all_values)
                                # Replace outlier value with mean
                                self.analyzer.analyses[key]['nodal'][electrode][variable] = mean_value
                                removed_count += 1
                
                elif metric_type == 'Pairwise':
                    # For pairwise metrics, we need to find the specific pairs
                    # This is handled similarly to nodal metrics
                    for pair, val in list(analysis['pairwise']['directional_pairs'].items()):
                        # Collect all non-outlier values for this pair
                        all_values = []
                        for _, other_analysis in self.analyzer.analyses.items():
                            if (other_analysis['metadata']['participant_id'], 
                                    other_analysis['metadata']['condition'], 
                                    other_analysis['metadata']['timepoint']) not in outliers_to_remove:
                                if pair in other_analysis['pairwise']['directional_pairs']:
                                    all_values.append(other_analysis['pairwise']['directional_pairs'][pair])
                        
                        # Calculate mean if we have enough values
                        if all_values:
                            mean_value = sum(all_values) / len(all_values)
                            # Replace outlier value with mean
                            self.analyzer.analyses[key]['pairwise']['directional_pairs'][pair] = mean_value
                            removed_count += 1
        
        # Refresh the outlier detection display
        self._detect_outliers()
        
        messagebox.showinfo("Outliers Removed", f"Successfully replaced {removed_count} outlier values with mean values.")

    def _run_normality_test(self):
        """Run Shapiro-Wilk normality test on the selected variable"""
        # Get selected variable and grouping
        metric_type = self.normality_metric_type.get()
        variable = self.normality_variable.get()
        group_by = self.normality_group.get()
        
        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return
        
        # Extract data
        df = self._extract_data_for_analysis(metric_type, variable)
        
        if df is None:
            return
        
        # Clear the treeview
        for item in self.normality_tree.get_children():
            self.normality_tree.delete(item)
        
        # Group the data if needed
        if group_by == 'none':
            # No grouping, run test on all data
            stat, p = stats.shapiro(df['Value'])
            is_normal = p > 0.05
            
            # Add to treeview
            values = ['All data', len(df), f"{stat:.4f}", f"{p:.4f}", "Yes" if is_normal else "No"]
            item_id = self.normality_tree.insert('', 'end', values=values)
            
            if not is_normal:
                self.normality_tree.item(item_id, tags=('not_normal',))
        
        elif group_by == 'condition':
            # Group by condition
            for condition, group in df.groupby('Condition'):
                if len(group) >= 3:  # Shapiro-Wilk needs at least 3 samples
                    stat, p = stats.shapiro(group['Value'])
                    is_normal = p > 0.05
                    
                    # Add to treeview
                    values = [f"Condition: {condition}", len(group), f"{stat:.4f}", f"{p:.4f}", "Yes" if is_normal else "No"]
                    item_id = self.normality_tree.insert('', 'end', values=values)
                    
                    if not is_normal:
                        self.normality_tree.item(item_id, tags=('not_normal',))
                else:
                    # Not enough samples
                    values = [f"Condition: {condition}", len(group), "N/A", "N/A", "N/A"]
                    self.normality_tree.insert('', 'end', values=values)
        
        elif group_by == 'timepoint':
            # Group by timepoint
            for timepoint, group in df.groupby('Timepoint'):
                if len(group) >= 3:  # Shapiro-Wilk needs at least 3 samples
                    stat, p = stats.shapiro(group['Value'])
                    is_normal = p > 0.05
                    
                    # Add to treeview
                    values = [f"Timepoint: {timepoint}", len(group), f"{stat:.4f}", f"{p:.4f}", "Yes" if is_normal else "No"]
                    item_id = self.normality_tree.insert('', 'end', values=values)
                    
                    if not is_normal:
                        self.normality_tree.item(item_id, tags=('not_normal',))
                else:
                    # Not enough samples
                    values = [f"Timepoint: {timepoint}", len(group), "N/A", "N/A", "N/A"]
                    self.normality_tree.insert('', 'end', values=values)
        
        elif group_by == 'both':
            # Group by condition and timepoint
            for (condition, timepoint), group in df.groupby(['Condition', 'Timepoint']):
                if len(group) >= 3:  # Shapiro-Wilk needs at least 3 samples
                    stat, p = stats.shapiro(group['Value'])
                    is_normal = p > 0.05
                    
                    # Add to treeview
                    values = [f"{condition}, {timepoint}", len(group), f"{stat:.4f}", f"{p:.4f}", "Yes" if is_normal else "No"]
                    item_id = self.normality_tree.insert('', 'end', values=values)
                    
                    if not is_normal:
                        self.normality_tree.item(item_id, tags=('not_normal',))
                else:
                    # Not enough samples
                    values = [f"{condition}, {timepoint}", len(group), "N/A", "N/A", "N/A"]
                    self.normality_tree.insert('', 'end', values=values)
        
        # Configure the tag
        self.normality_tree.tag_configure('not_normal', background='#ffcccc')
        
        # Show message
        messagebox.showinfo("Normality Test", "Shapiro-Wilk test completed. p > 0.05 indicates normal distribution.")
    
    def _export_normality_results(self):
        """Export normality test results to a CSV file"""
        if not self.normality_tree.get_children():
            messagebox.showwarning("No Results", "No normality test results to export")
            return
        
        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            title="Save Normality Test Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Collect data from treeview
        results = []
        for item_id in self.normality_tree.get_children():
            values = self.normality_tree.item(item_id, 'values')
            results.append({
                'Group': values[0],
                'N': values[1],
                'W_Statistic': values[2],
                'p-value': values[3],
                'Normal': values[4]
            })
        
        # Create dataframe and save to CSV
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        
        messagebox.showinfo("Export Complete", f"Normality test results saved to {file_path}")
    
    def _run_assumption_tests(self):
        """Run assumption tests for ANOVA"""
        # Get selected variable
        metric_type = self.assumption_metric_type.get()
        variable = self.assumption_variable.get()
        
        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return
        
        # Extract data
        df = self._extract_data_for_analysis(metric_type, variable)
        
        if df is None:
            return
        
        # Clear the treeview
        for item in self.assumption_tree.get_children():
            self.assumption_tree.delete(item)
        
        # Check which tests to run
        run_homogeneity = self.test_homogeneity.get()
        run_sphericity = self.test_sphericity.get()
        run_heteroscedasticity = self.test_heteroscedasticity.get()
        
        if run_homogeneity:
            # Levene's test for homogeneity of variance
            if 'Condition' in df.columns and len(df['Condition'].unique()) > 1:
                try:
                    # Group by condition
                    groups = [group['Value'].values for _, group in df.groupby('Condition')]
                    stat, p = stats.levene(*groups)
                    passed = p > 0.05
                    
                    # Add to treeview
                    values = ["Levene's Test (Condition)", f"{stat:.4f}", f"{p:.4f}", "Yes" if passed else "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    
                    if not passed:
                        self.assumption_tree.item(item_id, tags=('failed',))
                except Exception as e:
                    # Error running test
                    values = ["Levene's Test (Condition)", "Error", str(e), "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    self.assumption_tree.item(item_id, tags=('failed',))
            
            if 'Timepoint' in df.columns and len(df['Timepoint'].unique()) > 1:
                try:
                    # Group by timepoint
                    groups = [group['Value'].values for _, group in df.groupby('Timepoint')]
                    stat, p = stats.levene(*groups)
                    passed = p > 0.05
                    
                    # Add to treeview
                    values = ["Levene's Test (Timepoint)", f"{stat:.4f}", f"{p:.4f}", "Yes" if passed else "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    
                    if not passed:
                        self.assumption_tree.item(item_id, tags=('failed',))
                except Exception as e:
                    # Error running test
                    values = ["Levene's Test (Timepoint)", "Error", str(e), "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    self.assumption_tree.item(item_id, tags=('failed',))
        
        if run_sphericity and 'Participant' in df.columns and 'Timepoint' in df.columns and len(df['Timepoint'].unique()) > 1:
            try:
                # Prepare data for Mauchly's test (needs data in wide format)
                # First check if we have enough timepoints (at least 3 for sphericity to be meaningful)
                timepoints = sorted(df['Timepoint'].unique())
                
                if len(timepoints) < 3:
                    values = ["Mauchly's Test (Sphericity)", "N/A", "Need at least 3 timepoints", "N/A"]
                    self.assumption_tree.insert('', 'end', values=values)
                else:
                    # Convert to wide format (participant x timepoint)
                    wide_df = df.pivot_table(
                        index='Participant', 
                        columns='Timepoint', 
                        values='Value',
                        aggfunc='mean'  # In case there are duplicates
                    )
                    
                    # Check for missing values - sphericity test needs complete data
                    if wide_df.isna().any().any():
                        missing_count = wide_df.isna().sum().sum()
                        values = ["Mauchly's Test (Sphericity)", "N/A", f"Missing data: {missing_count} values", "N/A"]
                        self.assumption_tree.insert('', 'end', values=values)
                    else:
                        # Run Mauchly's test using pingouin
                        result = pg.sphericity(wide_df, method='mauchly')
                        
                        # Add results to treeview
                        w_stat = result.loc['sphericity', 'W']
                        chi2 = result.loc['sphericity', 'chi2']
                        dof = result.loc['sphericity', 'dof']
                        p_val = result.loc['sphericity', 'pval']
                        
                        passed = p_val > 0.05
                        
                        values = [
                            "Mauchly's Test (Sphericity)", 
                            f"W={w_stat:.4f}, χ²={chi2:.4f}, df={dof}", 
                            f"{p_val:.4f}", 
                            "Yes" if passed else "No"
                        ]
                        item_id = self.assumption_tree.insert('', 'end', values=values)
                        
                        if not passed:
                            self.assumption_tree.item(item_id, tags=('failed',))
                        
                        # Also add epsilon values (for correcting degrees of freedom if sphericity is violated)
                        for method in ['greenhouse', 'huynh', 'box']:
                            epsilon = float(result.loc[f'df_corr_{method}', 'W'])
                            values = [
                                f"Epsilon ({method.capitalize()})",
                                f"{epsilon:.4f}",
                                "Use to correct df when sphericity violated",
                                "N/A"
                            ]
                            self.assumption_tree.insert('', 'end', values=values)
            except Exception as e:
                # Error running test
                traceback.print_exc()
                values = ["Mauchly's Test (Sphericity)", "Error", str(e), "No"]
                item_id = self.assumption_tree.insert('', 'end', values=values)
                self.assumption_tree.item(item_id, tags=('failed',))
        
        if run_heteroscedasticity:
            # Breusch-Pagan test for heteroscedasticity
            # For simplicity, we'll run it on condition or timepoint if available
            try:
                if 'Condition' in df.columns and len(df['Condition'].unique()) > 1:
                    # Create dummy variables for condition
                    df_model = pd.get_dummies(df['Condition'], prefix='condition', drop_first=True)
                    df_model['Value'] = df['Value']
                    
                    # Fit the model
                    formula = 'Value ~ ' + ' + '.join([col for col in df_model.columns if col.startswith('condition')])
                    model = ols(formula, data=df_model).fit()
                    
                    # Run Breusch-Pagan test
                    bp_test = het_breuschpagan(model.resid, model.model.exog)
                    stat = bp_test[0]
                    p = bp_test[1]
                    passed = p > 0.05
                    
                    # Add to treeview
                    values = ["Breusch-Pagan (Condition)", f"{stat:.4f}", f"{p:.4f}", "Yes" if passed else "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    
                    if not passed:
                        self.assumption_tree.item(item_id, tags=('failed',))
                
                if 'Timepoint' in df.columns and len(df['Timepoint'].unique()) > 1:
                    # Create dummy variables for timepoint
                    df_model = pd.get_dummies(df['Timepoint'], prefix='timepoint', drop_first=True)
                    df_model['Value'] = df['Value']
                    
                    # Fit the model
                    formula = 'Value ~ ' + ' + '.join([col for col in df_model.columns if col.startswith('timepoint')])
                    model = ols(formula, data=df_model).fit()
                    
                    # Run Breusch-Pagan test
                    bp_test = het_breuschpagan(model.resid, model.model.exog)
                    stat = bp_test[0]
                    p = bp_test[1]
                    passed = p > 0.05
                    
                    # Add to treeview
                    values = ["Breusch-Pagan (Timepoint)", f"{stat:.4f}", f"{p:.4f}", "Yes" if passed else "No"]
                    item_id = self.assumption_tree.insert('', 'end', values=values)
                    
                    if not passed:
                        self.assumption_tree.item(item_id, tags=('failed',))
            except Exception as e:
                # Error running test
                values = ["Breusch-Pagan Test", "Error", str(e), "No"]
                item_id = self.assumption_tree.insert('', 'end', values=values)
                self.assumption_tree.item(item_id, tags=('failed',))
        
        # Configure the tag
        self.assumption_tree.tag_configure('failed', background='#ffcccc')
        
        # Show message
        messagebox.showinfo("Assumption Tests", "Assumption tests completed. p > 0.05 indicates the assumption is met.")
    
    def _export_assumption_results(self):
        """Export assumption test results to a CSV file"""
        if not self.assumption_tree.get_children():
            messagebox.showwarning("No Results", "No assumption test results to export")
            return
        
        # Similar to _export_normality_results
        file_path = filedialog.asksaveasfilename(
            title="Save Assumption Test Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Collect data from treeview
        results = []
        for item_id in self.assumption_tree.get_children():
            values = self.assumption_tree.item(item_id, 'values')
            results.append({
                'Test': values[0],
                'Statistic': values[1],
                'p-value': values[2],
                'Passed': values[3]
            })
        
        # Create dataframe and save to CSV
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        
        messagebox.showinfo("Export Complete", f"Assumption test results saved to {file_path}")
    
    def _run_anova(self):
        """Run ANOVA on the selected variable"""
        # Get selected variable and ANOVA type
        metric_type = self.anova_metric_type.get()
        variable = self.anova_variable.get()
        anova_type = self.anova_type.get()
        
        # Check which factors to include
        include_condition = self.factor_condition.get()
        include_timepoint = self.factor_timepoint.get()
        include_interaction = self.factor_interaction.get()
        
        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return
        
        # Extract data
        df = self._extract_data_for_analysis(metric_type, variable)
        
        if df is None:
            return
        
        # Clear the treeview
        for item in self.anova_tree.get_children():
            self.anova_tree.delete(item)
        
        # For factorial ANOVA
        if anova_type == 'factorial':
            try:
                # Check if we have enough data for meaningful analysis
                if len(df) < 4:
                    messagebox.showwarning("Insufficient Data", "At least 4 data points required for ANOVA")
                    return
                    
                # Make sure we have both factors if we want to test interaction
                if include_interaction and (not include_condition or not include_timepoint):
                    messagebox.showwarning("Invalid Selection", 
                                         "To test interaction, both Condition and Timepoint factors must be selected")
                    return
                
                # Prepare the formula based on selected factors
                formula_parts = []
                
                if include_condition and 'Condition' in df.columns and len(df['Condition'].unique()) > 1:
                    formula_parts.append('C(Condition)')
                
                if include_timepoint and 'Timepoint' in df.columns and len(df['Timepoint'].unique()) > 1:
                    formula_parts.append('C(Timepoint)')
                
                if include_interaction and include_condition and include_timepoint and \
                   'Condition' in df.columns and 'Timepoint' in df.columns and \
                   len(df['Condition'].unique()) > 1 and len(df['Timepoint'].unique()) > 1:
                    formula_parts.append('C(Condition):C(Timepoint)')
                
                if not formula_parts:
                    messagebox.showwarning("Invalid Selection", "Please select at least one factor for ANOVA")
                    return
                
                formula = 'Value ~ ' + ' + '.join(formula_parts)
                
                # Print formula for debugging
                print(f"ANOVA formula: {formula}")
                print(f"Data shape: {df.shape}")
                print(f"Data columns: {df.columns.tolist()}")
                
                # For nodal metrics, we may need to handle specific electrodes
                if metric_type == 'Nodal' and 'Electrode' in df.columns:
                    # Ask user if they want to analyze all electrodes or a specific one
                    unique_electrodes = sorted(df['Electrode'].unique())
                    
                    # Create a dialog to select electrode
                    electrode_dialog = tk.Toplevel(self.root)
                    electrode_dialog.title("Select Electrode")
                    electrode_dialog.geometry("400x300")
                    electrode_dialog.transient(self.root)
                    electrode_dialog.grab_set()
                    
                    ttk.Label(electrode_dialog, text="Choose Electrodes to Analyze:").pack(pady=10)
                    
                    # Create a frame for the listbox and scrollbar
                    list_frame = ttk.Frame(electrode_dialog)
                    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    # Create scrollbar
                    scrollbar = ttk.Scrollbar(list_frame)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Create listbox with multiple selection
                    electrode_listbox = tk.Listbox(list_frame, selectmode="multiple", yscrollcommand=scrollbar.set)
                    for electrode in unique_electrodes:
                        electrode_listbox.insert(tk.END, electrode)
                    electrode_listbox.pack(side="left", fill="both", expand=True)
                    
                    # Configure scrollbar
                    scrollbar.config(command=electrode_listbox.yview)
                    
                    # Add "All Electrodes" and "Selected Electrodes" options
                    option_frame = ttk.Frame(electrode_dialog)
                    option_frame.pack(fill="x", padx=10, pady=5)
                    
                    electrode_option = tk.StringVar(value="all")
                    ttk.Radiobutton(option_frame, text="All Electrodes (Average)", value="all", 
                                  variable=electrode_option).pack(anchor="w")
                    ttk.Radiobutton(option_frame, text="Selected Electrodes Only", value="selected", 
                                  variable=electrode_option).pack(anchor="w")
                    
                    # Add buttons
                    btn_frame = ttk.Frame(electrode_dialog)
                    btn_frame.pack(fill="x", padx=10, pady=10)
                    
                    result = [None, []]
                    
                    def on_ok():
                        selected_indices = electrode_listbox.curselection()
                        selected_electrodes = [electrode_listbox.get(i) for i in selected_indices]
                        result[0] = electrode_option.get()
                        result[1] = selected_electrodes
                        electrode_dialog.destroy()
                    
                    def on_cancel():
                        electrode_dialog.destroy()
                    
                    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="right", padx=5)
                    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=5)
                    
                    # Wait for dialog to close
                    self.root.wait_window(electrode_dialog)
                    
                    if result[0] is None:
                        return  # User canceled
                    
                    # Filter data based on selection
                    if result[0] == "selected" and result[1]:
                        df = df[df['Electrode'].isin(result[1])]
                        
                        if len(df) < 4:
                            messagebox.showwarning("Insufficient Data", 
                                                "Not enough data points for the selected electrodes")
                            return
                
                # For pairwise metrics, we may need to handle specific pairs
                if metric_type == 'Pairwise' and 'Pair' in df.columns:
                    # Similar to electrode selection dialog
                    unique_pairs = sorted(df['Pair'].unique())
                    
                    # Create a dialog to select pairs
                    pair_dialog = tk.Toplevel(self.root)
                    pair_dialog.title("Select Connection Pairs")
                    pair_dialog.geometry("500x400")
                    pair_dialog.transient(self.root)
                    pair_dialog.grab_set()
                    
                    ttk.Label(pair_dialog, text="Choose Connection Pairs to Analyze:").pack(pady=10)
                    
                    # Create a frame for the listbox and scrollbar
                    list_frame = ttk.Frame(pair_dialog)
                    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    # Create scrollbar
                    scrollbar = ttk.Scrollbar(list_frame)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Create listbox with multiple selection
                    pair_listbox = tk.Listbox(list_frame, selectmode="multiple", yscrollcommand=scrollbar.set)
                    for pair in unique_pairs:
                        pair_listbox.insert(tk.END, pair)
                    pair_listbox.pack(side="left", fill="both", expand=True)
                    
                    # Configure scrollbar
                    scrollbar.config(command=pair_listbox.yview)
                    
                    # Add "All Pairs" and "Selected Pairs" options
                    option_frame = ttk.Frame(pair_dialog)
                    option_frame.pack(fill="x", padx=10, pady=5)
                    
                    pair_option = tk.StringVar(value="all")
                    ttk.Radiobutton(option_frame, text="All Connection Pairs (Average)", value="all", 
                                  variable=pair_option).pack(anchor="w")
                    ttk.Radiobutton(option_frame, text="Selected Connection Pairs Only", value="selected", 
                                  variable=pair_option).pack(anchor="w")
                    ttk.Radiobutton(option_frame, text="Top 10 Strongest Connections", value="top10", 
                                  variable=pair_option).pack(anchor="w")
                    
                    # Add buttons
                    btn_frame = ttk.Frame(pair_dialog)
                    btn_frame.pack(fill="x", padx=10, pady=10)
                    
                    result = [None, []]
                    
                    def on_ok():
                        selected_indices = pair_listbox.curselection()
                        selected_pairs = [pair_listbox.get(i) for i in selected_indices]
                        result[0] = pair_option.get()
                        result[1] = selected_pairs
                        pair_dialog.destroy()
                    
                    def on_cancel():
                        pair_dialog.destroy()
                    
                    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="right", padx=5)
                    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=5)
                    
                    # Wait for dialog to close
                    self.root.wait_window(pair_dialog)
                    
                    if result[0] is None:
                        return  # User canceled
                    
                    # Filter data based on selection
                    if result[0] == "selected" and result[1]:
                        df = df[df['Pair'].isin(result[1])]
                    elif result[0] == "top10":
                        # Get the top 10 pairs by average value
                        pair_means = df.groupby('Pair')['Value'].mean().reset_index()
                        top_pairs = pair_means.nlargest(10, 'Value')['Pair'].tolist()
                        df = df[df['Pair'].isin(top_pairs)]
                        
                    if len(df) < 4:
                        messagebox.showwarning("Insufficient Data", 
                                            "Not enough data points for the selected pairs")
                        return
                
                # Fit the model
                model = ols(formula, data=df).fit()
                anova_table = anova_lm(model, typ=2)
                
                # Calculate effect sizes and observed power
                total_ss = anova_table['sum_sq'].sum()
                residual_df = anova_table.loc['Residual', 'df']
                
                for factor in anova_table.index:
                    if factor != 'Residual':
                        # Calculate partial eta squared
                        factor_ss = anova_table.loc[factor, 'sum_sq']
                        error_ss = anova_table.loc['Residual', 'sum_sq']
                        partial_eta_sq = factor_ss / (factor_ss + error_ss)
                        
                        # Calculate observed power
                        df_num = anova_table.loc[factor, 'df']
                        df_denom = residual_df
                        f_value = anova_table.loc[factor, 'F']
                        
                        # Use power calculation for F-test
                        power_calculator = FTestPower()
                        observed_power = power_calculator.power(f_val=f_value, df_num=df_num, df_denom=df_denom)
                        
                        # Calculate mean square
                        mean_sq = anova_table.loc[factor, 'sum_sq'] / anova_table.loc[factor, 'df']
                        
                        # Add to treeview
                        values = [
                            factor, 
                            f"{factor_ss:.4f}", 
                            f"{df_num:.0f}", 
                            f"{mean_sq:.4f}",
                            f"{f_value:.4f}", 
                            f"{anova_table.loc[factor, 'PR(>F)']:.4f}", 
                            f"{partial_eta_sq:.4f}",
                            f"{observed_power:.4f}"
                        ]
                        
                        item_id = self.anova_tree.insert('', 'end', values=values)
                        
                        # Color significant results
                        if anova_table.loc[factor, 'PR(>F)'] < 0.05:
                            self.anova_tree.item(item_id, tags=('significant',))
                
                # Add error term
                error_ss = anova_table.loc['Residual', 'sum_sq']
                error_df = anova_table.loc['Residual', 'df']
                error_ms = error_ss / error_df
                
                values = [
                    'Error', 
                    f"{error_ss:.4f}", 
                    f"{error_df:.0f}", 
                    f"{error_ms:.4f}",
                    '', '', '', ''
                ]
                
                self.anova_tree.insert('', 'end', values=values)
                
                # Add total
                values = [
                    'Total', 
                    f"{total_ss:.4f}", 
                    f"{sum(anova_table['df']):.0f}", 
                    '',
                    '', '', '', ''
                ]
                
                self.anova_tree.insert('', 'end', values=values)
                
                # Configure the tag
                self.anova_tree.tag_configure('significant', background='#ccffcc')
                
                # Show message about which data was analyzed
                if metric_type == 'Nodal':
                    if 'Electrode' in df.columns:
                        if result and result[0] == 'selected':
                            messagebox.showinfo("ANOVA Complete", 
                                             f"Factorial ANOVA completed for {variable} on {len(result[1])} electrodes: {', '.join(result[1])}")
                        else:
                            messagebox.showinfo("ANOVA Complete", 
                                             f"Factorial ANOVA completed for {variable} across all electrodes")
                elif metric_type == 'Pairwise':
                    if 'Pair' in df.columns:
                        if result and result[0] == 'selected':
                            messagebox.showinfo("ANOVA Complete", 
                                             f"Factorial ANOVA completed for {len(result[1])} connection pairs")
                        elif result and result[0] == 'top10':
                            messagebox.showinfo("ANOVA Complete", 
                                             f"Factorial ANOVA completed for top 10 strongest connection pairs")
                        else:
                            messagebox.showinfo("ANOVA Complete", 
                                             f"Factorial ANOVA completed for all connection pairs")
                else:
                    messagebox.showinfo("ANOVA Complete", "Factorial ANOVA completed successfully.")
                
            except Exception as e:
                print(f"ANOVA Error: {str(e)}")
                traceback.print_exc()
                messagebox.showerror("ANOVA Error", f"Error running ANOVA: {str(e)}")
        
        elif anova_type == 'repeated' or anova_type == 'mixed':
            # These are more complex, but we can implement them using pingouin
            try:
                # Check if we have the required factors and enough data
                if not include_timepoint or 'Timepoint' not in df.columns or len(df['Timepoint'].unique()) < 2:
                    messagebox.showwarning("Invalid Selection", 
                                        "Repeated measures and mixed ANOVA require 'Timepoint' factor with at least 2 levels")
                    return
                
                if 'Participant' not in df.columns or len(df['Participant'].unique()) < 2:
                    messagebox.showwarning("Insufficient Data", 
                                        "Repeated measures and mixed ANOVA require multiple participants")
                    return
                
                # For mixed ANOVA, we also need a between-subjects factor (Condition)
                if anova_type == 'mixed' and (not include_condition or 'Condition' not in df.columns or len(df['Condition'].unique()) < 2):
                    messagebox.showwarning("Invalid Selection", 
                                        "Mixed ANOVA requires 'Condition' factor with at least 2 levels")
                    return
                
                # Check for balanced design (pingouin's mixed_anova requires it)
                # Each participant should have data for all timepoints
                pivot_data = df.pivot_table(
                    index=['Participant', 'Condition'] if anova_type == 'mixed' else 'Participant',
                    columns='Timepoint',
                    values='Value',
                    aggfunc='mean'
                )
                
                if pivot_data.isna().any().any():
                    missing_count = pivot_data.isna().sum().sum()
                    messagebox.showwarning("Missing Data", 
                                        f"Design is not balanced. There are {missing_count} missing values.\n\n"
                                        "Repeated measures and mixed ANOVA require that each participant has data for all timepoints.")
                    return
                
                # For nodal metrics, we need to select specific electrodes
                if metric_type == 'Nodal' and 'Electrode' in df.columns:
                    unique_electrodes = sorted(df['Electrode'].unique())
                    
                    # Create a dialog to select electrode
                    electrode_dialog = tk.Toplevel(self.root)
                    electrode_dialog.title("Select Electrode")
                    electrode_dialog.geometry("400x300")
                    electrode_dialog.transient(self.root)
                    electrode_dialog.grab_set()
                    
                    ttk.Label(electrode_dialog, text="Choose an Electrode to Analyze:").pack(pady=10)
                    
                    # Create a frame for the listbox and scrollbar
                    list_frame = ttk.Frame(electrode_dialog)
                    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    # Create scrollbar
                    scrollbar = ttk.Scrollbar(list_frame)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Create listbox with single selection for RM ANOVA
                    electrode_listbox = tk.Listbox(list_frame, selectmode="single", yscrollcommand=scrollbar.set)
                    for electrode in unique_electrodes:
                        electrode_listbox.insert(tk.END, electrode)
                    electrode_listbox.pack(side="left", fill="both", expand=True)
                    
                    # Configure scrollbar
                    scrollbar.config(command=electrode_listbox.yview)
                    
                    # Add buttons
                    btn_frame = ttk.Frame(electrode_dialog)
                    btn_frame.pack(fill="x", padx=10, pady=10)
                    
                    selected_electrode = [None]
                    
                    def on_ok():
                        selected_indices = electrode_listbox.curselection()
                        if selected_indices:
                            selected_electrode[0] = electrode_listbox.get(selected_indices[0])
                        electrode_dialog.destroy()
                    
                    def on_cancel():
                        electrode_dialog.destroy()
                    
                    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="right", padx=5)
                    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=5)
                    
                    # Wait for dialog to close
                    self.root.wait_window(electrode_dialog)
                    
                    if selected_electrode[0] is None:
                        return  # User canceled
                    
                    # Filter data for selected electrode
                    df = df[df['Electrode'] == selected_electrode[0]]
                    
                    if df.empty:
                        messagebox.showwarning("No Data", f"No data for electrode {selected_electrode[0]}")
                        return
                
                # For pairwise metrics, we need to select a specific pair
                if metric_type == 'Pairwise' and 'Pair' in df.columns:
                    unique_pairs = sorted(df['Pair'].unique())
                    
                    # Create a dialog to select pairs
                    pair_dialog = tk.Toplevel(self.root)
                    pair_dialog.title("Select Connection Pair")
                    pair_dialog.geometry("500x400")
                    pair_dialog.transient(self.root)
                    pair_dialog.grab_set()
                    
                    ttk.Label(pair_dialog, text="Choose a Connection Pair to Analyze:").pack(pady=10)
                    
                    # Create a frame for the listbox and scrollbar
                    list_frame = ttk.Frame(pair_dialog)
                    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    
                    # Create scrollbar
                    scrollbar = ttk.Scrollbar(list_frame)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Create listbox with single selection for RM ANOVA
                    pair_listbox = tk.Listbox(list_frame, selectmode="single", yscrollcommand=scrollbar.set)
                    for pair in unique_pairs:
                        pair_listbox.insert(tk.END, pair)
                    pair_listbox.pack(side="left", fill="both", expand=True)
                    
                    # Configure scrollbar
                    scrollbar.config(command=pair_listbox.yview)
                    
                    # Add buttons
                    btn_frame = ttk.Frame(pair_dialog)
                    btn_frame.pack(fill="x", padx=10, pady=10)
                    
                    selected_pair = [None]
                    
                    def on_ok():
                        selected_indices = pair_listbox.curselection()
                        if selected_indices:
                            selected_pair[0] = pair_listbox.get(selected_indices[0])
                        pair_dialog.destroy()
                    
                    def on_cancel():
                        pair_dialog.destroy()
                    
                    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="right", padx=5)
                    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=5)
                    
                    # Wait for dialog to close
                    self.root.wait_window(pair_dialog)
                    
                    if selected_pair[0] is None:
                        return  # User canceled
                    
                    # Filter data for selected pair
                    df = df[df['Pair'] == selected_pair[0]]
                    
                    if df.empty:
                        messagebox.showwarning("No Data", f"No data for pair {selected_pair[0]}")
                        return
                
                # Run the appropriate analysis
                if anova_type == 'repeated':
                    # Repeated measures ANOVA using pingouin
                    result = pg.rm_anova(
                        data=df,
                        dv='Value',  # Dependent variable
                        within='Timepoint',  # Within-subjects factor
                        subject='Participant',  # Subject identifier
                        detailed=True  # Get detailed output
                    )
                    
                    # Add results to treeview
                    for idx, row in result.iterrows():
                        factor = row['Source']
                        
                        # Calculate partial eta squared (included in detailed output)
                        partial_eta_sq = row['np2']
                        
                        # Add to treeview
                        values = [
                            factor, 
                            f"{row['SS']:.4f}", 
                            f"{row['ddof1']:.0f}", 
                            f"{row['MS']:.4f}",
                            f"{row['F']:.4f}", 
                            f"{row['p-unc']:.4f}", 
                            f"{partial_eta_sq:.4f}",
                            "N/A"  # Pingouin doesn't calculate observed power
                        ]
                        
                        item_id = self.anova_tree.insert('', 'end', values=values)
                        
                        # Color significant results
                        if row['p-unc'] < 0.05:
                            self.anova_tree.item(item_id, tags=('significant',))
                    
                    # Configure the tag
                    self.anova_tree.tag_configure('significant', background='#ccffcc')
                    
                    # Show message
                    if metric_type == 'Nodal':
                        messagebox.showinfo("ANOVA Complete", 
                                         f"Repeated Measures ANOVA completed for electrode {selected_electrode[0]}")
                    elif metric_type == 'Pairwise':
                        messagebox.showinfo("ANOVA Complete", 
                                         f"Repeated Measures ANOVA completed for connection pair {selected_pair[0]}")
                    else:
                        messagebox.showinfo("ANOVA Complete", 
                                         "Repeated Measures ANOVA completed successfully")
                    
                elif anova_type == 'mixed':
                    # Mixed ANOVA using pingouin
                    result = pg.mixed_anova(
                        data=df,
                        dv='Value',  # Dependent variable
                        between='Condition',  # Between-subjects factor
                        within='Timepoint',  # Within-subjects factor
                        subject='Participant',  # Subject identifier
                        detailed=True  # Get detailed output
                    )
                    
                    # Add results to treeview
                    for idx, row in result.iterrows():
                        factor = row['Source']
                        
                        # Calculate partial eta squared (included in detailed output)
                        partial_eta_sq = row['np2']
                        
                        # Add to treeview
                        values = [
                            factor, 
                            f"{row['SS']:.4f}", 
                            f"{row['DF1']:.0f}", 
                            f"{row['MS']:.4f}",
                            f"{row['F']:.4f}", 
                            f"{row['p-unc']:.4f}", 
                            f"{partial_eta_sq:.4f}",
                            "N/A"  # Pingouin doesn't calculate observed power
                        ]
                        
                        item_id = self.anova_tree.insert('', 'end', values=values)
                        
                        # Color significant results
                        if row['p-unc'] < 0.05:
                            self.anova_tree.item(item_id, tags=('significant',))
                    
                    # Configure the tag
                    self.anova_tree.tag_configure('significant', background='#ccffcc')
                    
                    # Show message
                    if metric_type == 'Nodal':
                        messagebox.showinfo("ANOVA Complete", 
                                         f"Mixed ANOVA completed for electrode {selected_electrode[0]}")
                    elif metric_type == 'Pairwise':
                        messagebox.showinfo("ANOVA Complete", 
                                         f"Mixed ANOVA completed for connection pair {selected_pair[0]}")
                    else:
                        messagebox.showinfo("ANOVA Complete", 
                                         "Mixed ANOVA completed successfully")
                
            except Exception as e:
                print(f"Repeated/Mixed ANOVA Error: {str(e)}")
                traceback.print_exc()
                messagebox.showerror("ANOVA Error", f"Error running {anova_type.capitalize()} ANOVA: {str(e)}")
    
    def _export_anova_results(self):
        """Export ANOVA results to a CSV file"""
        if not self.anova_tree.get_children():
            messagebox.showwarning("No Results", "No ANOVA results to export")
            return
        
        # Similar to other export functions
        file_path = filedialog.asksaveasfilename(
            title="Save ANOVA Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Collect data from treeview
        results = []
        for item_id in self.anova_tree.get_children():
            values = self.anova_tree.item(item_id, 'values')
            results.append({
                'Source': values[0],
                'Sum of Squares': values[1],
                'df': values[2],
                'Mean Square': values[3],
                'F': values[4],
                'p_value': values[5],
                'Partial_Eta_Squared': values[6],
                'Observed_Power': values[7]
            })
        
        # Create dataframe and save to CSV
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        
        messagebox.showinfo("Export Complete", f"ANOVA results saved to {file_path}")
    
    def _run_posthoc_test(self):
        """Run post-hoc test on the selected variable"""
        # Get selected variable, test type, and factor
        metric_type = self.posthoc_metric_type.get()
        variable = self.posthoc_variable.get()
        test_type = self.posthoc_test.get()
        factor = self.posthoc_factor.get()
        
        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return
        
        # Extract data
        df = self._extract_data_for_analysis(metric_type, variable)
        
        if df is None:
            return
        
        # Clear the treeview
        for item in self.posthoc_tree.get_children():
            self.posthoc_tree.delete(item)
        
        try:
            if factor == 'condition' and 'Condition' in df.columns:
                # Run post-hoc test for condition
                posthoc = MultiComparison(df['Value'], df['Condition'])
                
                if test_type == 'bonferroni':
                    result = posthoc.allpairtest(stats.ttest_ind, method='bonf')
                else:  # tukey
                    result = posthoc.tukeyhsd()
                
                # Add results to treeview
                self._add_posthoc_results_to_tree(result, test_type)
                
            elif factor == 'timepoint' and 'Timepoint' in df.columns:
                # Run post-hoc test for timepoint
                posthoc = MultiComparison(df['Value'], df['Timepoint'])
                
                if test_type == 'bonferroni':
                    result = posthoc.allpairtest(stats.ttest_ind, method='bonf')
                else:  # tukey
                    result = posthoc.tukeyhsd()
                
                # Add results to treeview
                self._add_posthoc_results_to_tree(result, test_type)
                
            elif factor == 'interaction' and 'Condition' in df.columns and 'Timepoint' in df.columns:
                # Create interaction groups
                df['Group'] = df['Condition'] + '_' + df['Timepoint']
                
                # Run post-hoc test for interaction
                posthoc = MultiComparison(df['Value'], df['Group'])
                
                if test_type == 'bonferroni':
                    result = posthoc.allpairtest(stats.ttest_ind, method='bonf')
                else:  # tukey
                    result = posthoc.tukeyhsd()
                
                # Add results to treeview
                self._add_posthoc_results_to_tree(result, test_type)
                
            else:
                messagebox.showwarning("Invalid Selection", f"Cannot perform post-hoc test for factor: {factor}")
                return
                
        except Exception as e:
            messagebox.showerror("Post-hoc Test Error", f"Error running post-hoc test: {str(e)}")
    
    def _add_posthoc_results_to_tree(self, result, test_type):
        """Add post-hoc test results to the treeview"""
        if test_type == 'bonferroni':
            # For bonferroni correction
            for i, test_result in enumerate(result[0]):
                group1, group2 = result[1][i]
                p_value = test_result[1]
                t_value = test_result[0]
                mean_diff = test_result[2]
                std_error = test_result[3] if len(test_result) > 3 else 'N/A'
                
                is_significant = p_value < 0.05
                
                values = [
                    group1, 
                    group2, 
                    f"{mean_diff:.4f}", 
                    std_error,
                    f"{t_value:.4f}", 
                    f"{p_value:.4f}", 
                    "Yes" if is_significant else "No"
                ]
                
                item_id = self.posthoc_tree.insert('', 'end', values=values)
                
                if is_significant:
                    self.posthoc_tree.item(item_id, tags=('significant',))
        else:
            # For Tukey's HSD
            for i, (group1, group2, mean_diff, p_value, conf_lower, conf_upper) in enumerate(result._results_table.data[1:]):
                std_error = result.std_pairs
                t_value = mean_diff / std_error if std_error > 0 else 'N/A'
                
                is_significant = p_value < 0.05
                
                values = [
                    group1, 
                    group2, 
                    f"{mean_diff:.4f}", 
                    f"{std_error:.4f}",
                    t_value if isinstance(t_value, str) else f"{t_value:.4f}", 
                    f"{p_value:.4f}", 
                    "Yes" if is_significant else "No"
                ]
                
                item_id = self.posthoc_tree.insert('', 'end', values=values)
                
                if is_significant:
                    self.posthoc_tree.item(item_id, tags=('significant',))
        
        # Configure the tag
        self.posthoc_tree.tag_configure('significant', background='#ccffcc')
        
        # Show message
        messagebox.showinfo("Post-hoc Test Complete", f"{test_type.capitalize()} post-hoc test completed successfully.")
    
    def _export_posthoc_results(self):
        """Export post-hoc test results to a CSV file"""
        if not self.posthoc_tree.get_children():
            messagebox.showwarning("No Results", "No post-hoc test results to export")
            return
        
        # Similar to other export functions
        file_path = filedialog.asksaveasfilename(
            title="Save Post-hoc Test Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Collect data from treeview
        results = []
        for item_id in self.posthoc_tree.get_children():
            values = self.posthoc_tree.item(item_id, 'values')
            results.append({
                'Group_1': values[0],
                'Group_2': values[1],
                'Mean_Diff': values[2],
                'Std_Error': values[3],
                't_value': values[4],
                'p_value': values[5],
                'Significant': values[6]
            })
        
        # Create dataframe and save to CSV
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        
        messagebox.showinfo("Export Complete", f"Post-hoc test results saved to {file_path}")

def main():
    root = tk.Tk()
    app = GrangerAnalysisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 