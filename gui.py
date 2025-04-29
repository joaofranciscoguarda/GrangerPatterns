import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys
from pathlib import Path
import numpy as np
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
        
        ttk.Label(options_frame, text="Visualization Level:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.viz_level = tk.StringVar(value="Individual")
        viz_level_combo = ttk.Combobox(options_frame, textvariable=self.viz_level)
        viz_level_combo['values'] = ('Individual', 'Condition', 'Timepoint', 'Condition × Timepoint')
        viz_level_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(options_frame, text="Metric Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.metric_type = tk.StringVar(value="Global")
        metric_type_combo = ttk.Combobox(options_frame, textvariable=self.metric_type)
        metric_type_combo['values'] = ('Global', 'Nodal', 'Network', 'Pairwise', 'Matrix')
        metric_type_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Visualization buttons
        btn_frame = ttk.Frame(viz_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Generate Visualization", command=self.generate_visualization).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Visualizations", command=self.export_visualizations).pack(side="left", padx=5)
        
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
        """Generate visualizations based on the selected options"""
        if not self.analyzer.analyses:
            messagebox.showwarning("No Analyses", "No analyses available. Please analyze data first.")
            return
        
        # Get selected visualization level and metric type
        level = self.viz_level.get()
        metric_type = self.metric_type.get()
        
        try:
            # Implement visualization based on level and metric type
            # This would call appropriate visualization methods based on the selections
            messagebox.showinfo("Visualization", f"Generating {metric_type} visualization at {level} level")
            
            # This is a placeholder - actual implementation would depend on your visualization modules
            
        except Exception as e:
            messagebox.showerror("Visualization Error", f"Error generating visualization: {str(e)}")
    
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
        
        # TODO: Implement outlier removal from the dataset
        # This is more complex as it requires modifying the original data in the analyzer
        # For now, just show a message
        messagebox.showinfo("Not Implemented", "Outlier removal is not yet implemented. This would require modifying the original dataset.")
    
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
        
        if run_sphericity and 'Participant' in df.columns and 'Timepoint' in df.columns:
            # Mauchly's test for sphericity (for repeated measures)
            # This is complex and requires a specific data structure
            # For simplicity, we'll just note it's not implemented yet
            values = ["Mauchly's Test (Sphericity)", "N/A", "Not implemented", "N/A"]
            self.assumption_tree.insert('', 'end', values=values)
        
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
                # Prepare the formula based on selected factors
                formula_parts = []
                
                if include_condition and 'Condition' in df.columns:
                    formula_parts.append('C(Condition)')
                
                if include_timepoint and 'Timepoint' in df.columns:
                    formula_parts.append('C(Timepoint)')
                
                if include_interaction and include_condition and include_timepoint and 'Condition' in df.columns and 'Timepoint' in df.columns:
                    formula_parts.append('C(Condition):C(Timepoint)')
                
                if not formula_parts:
                    messagebox.showwarning("Invalid Selection", "Please select at least one factor for ANOVA")
                    return
                
                formula = 'Value ~ ' + ' + '.join(formula_parts)
                
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
                
                # Show message
                messagebox.showinfo("ANOVA Complete", "Factorial ANOVA completed successfully.")
                
            except Exception as e:
                messagebox.showerror("ANOVA Error", f"Error running ANOVA: {str(e)}")
        
        elif anova_type == 'repeated' or anova_type == 'mixed':
            # These are more complex and require specific data structure
            messagebox.showinfo("Not Implemented", 
                              f"{anova_type.capitalize()} Measures ANOVA is not yet implemented. "
                              "This requires a specialized analysis approach.")
    
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