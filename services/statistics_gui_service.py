#!/usr/bin/env python3
"""
Statistics GUI Service for Granger Causality Analysis

This service provides GUI components for the statistics window including:
- Tab creation and management
- Variable selection widgets
- Results display components
- Export functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
import os

from .statistics_service import get_statistics_service


class StatisticsGUIService:
    """Service for statistics GUI components and operations"""

    def __init__(self, parent_window, analyzer):
        self.parent = parent_window
        self.analyzer = analyzer
        self.stats_service = get_statistics_service()

        # Variables for each tab
        self.outlier_vars = {}
        self.normality_vars = {}
        self.assumption_vars = {}
        self.anova_vars = {}
        self.posthoc_vars = {}
        self.paired_test_vars = {}

        # Treeviews for results
        self.trees = {}

        # Current results for export
        self.current_results = {}

    def create_outlier_tab(self, parent) -> None:
        """Create outlier detection tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.outlier_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.outlier_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.outlier_vars["variable"] = tk.StringVar()
        self.outlier_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.outlier_vars["variable"]
        )
        self.outlier_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_outlier_variables)

        # Detection method frame
        method_frame = ttk.LabelFrame(parent, text="Detection Method")
        method_frame.pack(fill="x", padx=10, pady=5)

        self.outlier_vars["method"] = tk.StringVar(value="z_score")
        ttk.Radiobutton(
            method_frame,
            text="Z-Score (±3 SD)",
            value="z_score",
            variable=self.outlier_vars["method"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            method_frame,
            text="IQR (1.5 × IQR)",
            value="iqr",
            variable=self.outlier_vars["method"],
        ).pack(anchor="w", padx=20, pady=2)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Detect Outliers", command=self._detect_outliers
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Apply Mean Imputation", command=self._remove_outliers
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_outlier_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for outlier results
        columns = ("Participant", "Condition", "Timepoint", "Value", "Status")
        self.trees["outlier"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["outlier"].heading(col, text=col)
            self.trees["outlier"].column(col, width=100, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["outlier"].yview
        )
        self.trees["outlier"].configure(yscrollcommand=y_scroll.set)

        # Pack elements
        self.trees["outlier"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_outlier_variables()

    def create_normality_tab(self, parent) -> None:
        """Create normality test tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.normality_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.normality_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.normality_vars["variable"] = tk.StringVar()
        self.normality_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.normality_vars["variable"]
        )
        self.normality_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Grouping frame
        group_frame = ttk.LabelFrame(parent, text="Group By")
        group_frame.pack(fill="x", padx=10, pady=5)

        self.normality_vars["group"] = tk.StringVar(value="none")
        ttk.Radiobutton(
            group_frame,
            text="No Grouping",
            value="none",
            variable=self.normality_vars["group"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            group_frame,
            text="Condition",
            value="condition",
            variable=self.normality_vars["group"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            group_frame,
            text="Timepoint",
            value="timepoint",
            variable=self.normality_vars["group"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            group_frame,
            text="Condition × Timepoint",
            value="both",
            variable=self.normality_vars["group"],
        ).pack(anchor="w", padx=20, pady=2)

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_normality_variables)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Run Shapiro-Wilk Test", command=self._run_normality_test
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_normality_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for normality results
        columns = ("Group", "N", "W Statistic", "p-value", "Normal")
        self.trees["normality"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["normality"].heading(col, text=col)
            self.trees["normality"].column(col, width=100, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["normality"].yview
        )
        self.trees["normality"].configure(yscrollcommand=y_scroll.set)

        # Pack elements
        self.trees["normality"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_normality_variables()

    def create_assumption_tab(self, parent) -> None:
        """Create assumption tests tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.assumption_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.assumption_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.assumption_vars["variable"] = tk.StringVar()
        self.assumption_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.assumption_vars["variable"]
        )
        self.assumption_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_assumption_variables)

        # Test selection frame
        test_frame = ttk.LabelFrame(parent, text="Tests to Run")
        test_frame.pack(fill="x", padx=10, pady=5)

        self.assumption_vars["test_homogeneity"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            test_frame,
            text="Homogeneity of Variance (Levene's Test)",
            variable=self.assumption_vars["test_homogeneity"],
        ).pack(anchor="w", padx=20, pady=2)

        self.assumption_vars["test_sphericity"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            test_frame,
            text="Sphericity (Mauchly's Test) - for repeated measures",
            variable=self.assumption_vars["test_sphericity"],
        ).pack(anchor="w", padx=20, pady=2)

        self.assumption_vars["test_heteroscedasticity"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            test_frame,
            text="Heteroscedasticity (Breusch-Pagan Test)",
            variable=self.assumption_vars["test_heteroscedasticity"],
        ).pack(anchor="w", padx=20, pady=2)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Run Tests", command=self._run_assumption_tests
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_assumption_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for assumption test results
        columns = ("Test", "Statistic", "p-value", "Passed")
        self.trees["assumption"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["assumption"].heading(col, text=col)
            self.trees["assumption"].column(
                col, width=150 if col == "Test" else 100, anchor="center"
            )

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["assumption"].yview
        )
        self.trees["assumption"].configure(yscrollcommand=y_scroll.set)

        # Pack elements
        self.trees["assumption"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_assumption_variables()

    def create_anova_tab(self, parent) -> None:
        """Create ANOVA tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.anova_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.anova_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.anova_vars["variable"] = tk.StringVar()
        self.anova_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.anova_vars["variable"]
        )
        self.anova_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_anova_variables)

        # ANOVA Type frame
        type_frame = ttk.LabelFrame(parent, text="ANOVA Type")
        type_frame.pack(fill="x", padx=10, pady=5)

        self.anova_vars["type"] = tk.StringVar(value="factorial")
        ttk.Radiobutton(
            type_frame,
            text="Factorial ANOVA (Between-subjects)",
            value="factorial",
            variable=self.anova_vars["type"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            type_frame,
            text="Repeated Measures ANOVA",
            value="repeated",
            variable=self.anova_vars["type"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            type_frame,
            text="Mixed ANOVA",
            value="mixed",
            variable=self.anova_vars["type"],
        ).pack(anchor="w", padx=20, pady=2)

        # Factors frame
        factors_frame = ttk.LabelFrame(parent, text="Factors")
        factors_frame.pack(fill="x", padx=10, pady=5)

        self.anova_vars["factor_condition"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            factors_frame,
            text="Condition",
            variable=self.anova_vars["factor_condition"],
        ).pack(anchor="w", padx=20, pady=2)

        self.anova_vars["factor_timepoint"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            factors_frame,
            text="Timepoint",
            variable=self.anova_vars["factor_timepoint"],
        ).pack(anchor="w", padx=20, pady=2)

        self.anova_vars["factor_group"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            factors_frame,
            text="Group (Between-Subjects Factor)",
            variable=self.anova_vars["factor_group"],
        ).pack(anchor="w", padx=20, pady=2)

        self.anova_vars["factor_interaction"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            factors_frame,
            text="Condition × Timepoint Interaction",
            variable=self.anova_vars["factor_interaction"],
        ).pack(anchor="w", padx=20, pady=2)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="Run ANOVA", command=self._run_anova).pack(
            side="left", padx=5
        )
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_anova_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for ANOVA results
        columns = (
            "Source",
            "Sum of Squares",
            "df",
            "Mean Square",
            "F",
            "p-value",
            "Partial η²",
            "Observed Power",
        )
        self.trees["anova"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["anova"].heading(col, text=col)
            width = 150 if col == "Source" else 100
            self.trees["anova"].column(col, width=width, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["anova"].yview
        )
        self.trees["anova"].configure(yscrollcommand=y_scroll.set)

        # Pack elements
        self.trees["anova"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_anova_variables()

    def create_posthoc_tab(self, parent) -> None:
        """Create post-hoc tests tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.posthoc_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.posthoc_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.posthoc_vars["variable"] = tk.StringVar()
        self.posthoc_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.posthoc_vars["variable"]
        )
        self.posthoc_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_posthoc_variables)

        # Post-hoc test type frame
        test_frame = ttk.LabelFrame(parent, text="Post-hoc Test")
        test_frame.pack(fill="x", padx=10, pady=5)

        self.posthoc_vars["test"] = tk.StringVar(value="tukey")
        ttk.Radiobutton(
            test_frame,
            text="Tukey HSD",
            value="tukey",
            variable=self.posthoc_vars["test"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            test_frame,
            text="Bonferroni",
            value="bonferroni",
            variable=self.posthoc_vars["test"],
        ).pack(anchor="w", padx=20, pady=2)

        # Factor selection frame
        factor_frame = ttk.LabelFrame(parent, text="Factor")
        factor_frame.pack(fill="x", padx=10, pady=5)

        self.posthoc_vars["factor"] = tk.StringVar(value="condition")
        ttk.Radiobutton(
            factor_frame,
            text="Condition",
            value="condition",
            variable=self.posthoc_vars["factor"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            factor_frame,
            text="Timepoint",
            value="timepoint",
            variable=self.posthoc_vars["factor"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            factor_frame,
            text="Condition × Timepoint",
            value="interaction",
            variable=self.posthoc_vars["factor"],
        ).pack(anchor="w", padx=20, pady=2)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Run Post-hoc Test", command=self._run_posthoc_test
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_posthoc_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for post-hoc results
        columns = (
            "Group 1",
            "Group 2",
            "Mean Diff",
            "Std Error",
            "t-value",
            "p-value",
            "Significant",
        )
        self.trees["posthoc"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["posthoc"].heading(col, text=col)
            self.trees["posthoc"].column(col, width=100, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["posthoc"].yview
        )
        self.trees["posthoc"].configure(yscrollcommand=y_scroll.set)

        # Pack elements
        self.trees["posthoc"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_posthoc_variables()

    def create_paired_test_tab(self, parent) -> None:
        """Create paired tests tab content"""
        # Variable selection frame
        selection_frame = ttk.LabelFrame(parent, text="Variable Selection")
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Metric Type:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.paired_test_vars["metric_type"] = tk.StringVar(value="Global")
        metric_combo = ttk.Combobox(
            selection_frame, textvariable=self.paired_test_vars["metric_type"]
        )
        metric_combo["values"] = ("Global", "Nodal", "Pairwise")
        metric_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(selection_frame, text="Variable:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.paired_test_vars["variable"] = tk.StringVar()
        self.paired_test_vars["variable_combo"] = ttk.Combobox(
            selection_frame, textvariable=self.paired_test_vars["variable"]
        )
        self.paired_test_vars["variable_combo"].grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Update variables when metric type changes
        metric_combo.bind("<<ComboboxSelected>>", self._update_paired_test_variables)

        # Test type frame
        test_frame = ttk.LabelFrame(parent, text="Test Type")
        test_frame.pack(fill="x", padx=10, pady=5)

        self.paired_test_vars["test_type"] = tk.StringVar(value="paired_t")
        ttk.Radiobutton(
            test_frame,
            text="Paired t-test (parametric)",
            value="paired_t",
            variable=self.paired_test_vars["test_type"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            test_frame,
            text="Wilcoxon signed-rank test (non-parametric)",
            value="wilcoxon",
            variable=self.paired_test_vars["test_type"],
        ).pack(anchor="w", padx=20, pady=2)

        # Grouping factor frame
        factor_frame = ttk.LabelFrame(parent, text="Pairing Factor")
        factor_frame.pack(fill="x", padx=10, pady=5)

        self.paired_test_vars["group_factor"] = tk.StringVar(value="Timepoint")
        ttk.Radiobutton(
            factor_frame,
            text="Timepoint (compare across time)",
            value="Timepoint",
            variable=self.paired_test_vars["group_factor"],
        ).pack(anchor="w", padx=20, pady=2)
        ttk.Radiobutton(
            factor_frame,
            text="Condition (compare across conditions)",
            value="Condition",
            variable=self.paired_test_vars["group_factor"],
        ).pack(anchor="w", padx=20, pady=2)

        # Information frame
        info_frame = ttk.LabelFrame(parent, text="Information")
        info_frame.pack(fill="x", padx=10, pady=5)

        info_text = (
            "• Paired tests compare related observations (same participants)\n"
            "• Use paired t-test when differences are normally distributed\n"
            "• Use Wilcoxon test when data violates normality assumptions\n"
            "• Only participants with data in all groups will be included"
        )
        ttk.Label(info_frame, text=info_text, justify="left").pack(
            anchor="w", padx=20, pady=10
        )

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame, text="Run Paired Tests", command=self._run_paired_tests
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Export Results", command=self._export_paired_test_results
        ).pack(side="left", padx=5)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview for paired test results
        columns = (
            "Comparison",
            "Test",
            "N",
            "Statistic",
            "p-value",
            "Effect Size",
            "95% CI Lower",
            "95% CI Upper",
            "Significant",
        )
        self.trees["paired_test"] = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        # Configure columns
        for col in columns:
            self.trees["paired_test"].heading(col, text=col)
            width = 120 if col in ["Comparison", "Test"] else 90
            self.trees["paired_test"].column(col, width=width, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.trees["paired_test"].yview
        )
        self.trees["paired_test"].configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(
            results_frame, orient="horizontal", command=self.trees["paired_test"].xview
        )
        self.trees["paired_test"].configure(xscrollcommand=x_scroll.set)

        # Pack elements
        self.trees["paired_test"].pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")

        # Configure grid weights
        selection_frame.columnconfigure(1, weight=1)

        # Initial variable update
        self._update_paired_test_variables()

    # Variable update methods
    def _update_outlier_variables(self, event=None):
        """Update available variables for outlier detection"""
        metric_type = self.outlier_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.outlier_vars["variable_combo"]["values"] = variables
        if variables:
            self.outlier_vars["variable"].set(variables[0])

    def _update_normality_variables(self, event=None):
        """Update available variables for normality testing"""
        metric_type = self.normality_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.normality_vars["variable_combo"]["values"] = variables
        if variables:
            self.normality_vars["variable"].set(variables[0])

    def _update_assumption_variables(self, event=None):
        """Update available variables for assumption testing"""
        metric_type = self.assumption_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.assumption_vars["variable_combo"]["values"] = variables
        if variables:
            self.assumption_vars["variable"].set(variables[0])

    def _update_anova_variables(self, event=None):
        """Update available variables for ANOVA"""
        metric_type = self.anova_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.anova_vars["variable_combo"]["values"] = variables
        if variables:
            self.anova_vars["variable"].set(variables[0])

    def _update_posthoc_variables(self, event=None):
        """Update available variables for post-hoc testing"""
        metric_type = self.posthoc_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.posthoc_vars["variable_combo"]["values"] = variables
        if variables:
            self.posthoc_vars["variable"].set(variables[0])

    def _update_paired_test_variables(self, event=None):
        """Update available variables for paired testing"""
        metric_type = self.paired_test_vars["metric_type"].get()
        variables = self.stats_service.get_available_variables(
            self.analyzer, metric_type
        )
        self.paired_test_vars["variable_combo"]["values"] = variables
        if variables:
            self.paired_test_vars["variable"].set(variables[0])

    # Analysis methods
    def _detect_outliers(self):
        """Detect outliers in the selected variable"""
        metric_type = self.outlier_vars["metric_type"].get()
        variable = self.outlier_vars["variable"].get()
        method = self.outlier_vars["method"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Clear the treeview
        for item in self.trees["outlier"].get_children():
            self.trees["outlier"].delete(item)

        # Detect outliers
        if method == "z_score":
            result_df = self.stats_service.detect_outliers_zscore(df)
        else:  # iqr
            result_df = self.stats_service.detect_outliers_iqr(df)

        # Populate treeview
        outlier_count = 0
        for _, row in result_df.iterrows():
            is_outlier = row["is_outlier"]
            status = "Outlier" if is_outlier else "Normal"

            values = [
                row["Participant"],
                row["Condition"],
                row["Timepoint"],
                f"{row['Value']:.4f}",
                status,
            ]

            item_id = self.trees["outlier"].insert("", "end", values=values)

            if is_outlier:
                self.trees["outlier"].item(item_id, tags=("outlier",))
                outlier_count += 1

        # Configure the tag
        self.trees["outlier"].tag_configure("outlier", background="#ffcccc")

        # Store results for export
        self.current_results["outlier"] = result_df

        # Show summary
        method_name = "Z-Score (±3 SD)" if method == "z_score" else "IQR (1.5 × IQR)"
        messagebox.showinfo(
            "Outlier Detection",
            f"Detected {outlier_count} outliers using {method_name} method",
        )

    def _remove_outliers(self):
        """Remove outliers by replacing with mean values using mean imputation"""
        if "outlier" not in self.current_results:
            messagebox.showwarning("No Results", "Please run outlier detection first")
            return

        # Get the outlier data
        outlier_df = self.current_results["outlier"]
        outlier_count = outlier_df["is_outlier"].sum()

        if outlier_count == 0:
            messagebox.showinfo("No Outliers", "No outliers found to remove")
            return

        # Calculate the mean of non-outlier values for display
        non_outlier_mean = outlier_df.loc[~outlier_df["is_outlier"], "Value"].mean()

        # Ask user for confirmation with detailed information
        response = messagebox.askyesno(
            "Confirm Mean Imputation for Outliers",
            f"Mean Imputation Process:\n\n"
            f"• Found {outlier_count} outlier value(s)\n"
            f"• Mean of non-outlier values: {non_outlier_mean:.4f}\n"
            f"• Each outlier will be replaced with this mean value\n"
            f"• This neutralizes the effect of extreme outliers\n\n"
            "Do you want to continue with mean imputation?",
        )

        if not response:
            return

        # Remove outliers using mean imputation
        cleaned_df, removed_count = self.stats_service.remove_outliers(
            outlier_df, method="mean"
        )

        if removed_count > 0:
            # Update the current results with cleaned data
            self.current_results["outlier"] = cleaned_df

            # Refresh the treeview to show updated values
            for item in self.trees["outlier"].get_children():
                self.trees["outlier"].delete(item)

            # Populate treeview with cleaned data
            for _, row in cleaned_df.iterrows():
                is_outlier = row["is_outlier"]
                status = "Imputed (Mean)" if is_outlier else "Normal"

                # Show imputed mean value for outliers
                display_value = row["Value"]

                values = [
                    row["Participant"],
                    row["Condition"],
                    row["Timepoint"],
                    f"{display_value:.4f}",
                    status,
                ]

                item_id = self.trees["outlier"].insert("", "end", values=values)

                if is_outlier:
                    self.trees["outlier"].item(item_id, tags=("removed",))

            # Configure the tag for removed outliers
            self.trees["outlier"].tag_configure("removed", background="#ffffcc")

            messagebox.showinfo(
                "Mean Imputation Complete",
                f"Successfully applied mean imputation to {removed_count} outlier values.\n\n"
                f"• Outliers replaced with mean value: {non_outlier_mean:.4f}\n"
                f"• Extreme values have been neutralized\n"
                f"• Yellow highlighted rows show imputed values\n\n"
                "The data display has been updated to show the cleaned values.",
            )
        else:
            messagebox.showinfo("No Outliers", "No outliers found to remove")

    def _run_normality_test(self):
        """Run Shapiro-Wilk normality test"""
        metric_type = self.normality_vars["metric_type"].get()
        variable = self.normality_vars["variable"].get()
        group_by = self.normality_vars["group"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Clear the treeview
        for item in self.trees["normality"].get_children():
            self.trees["normality"].delete(item)

        # Run normality tests
        results = self.stats_service.test_normality(df, group_by)

        # Populate treeview
        for result in results:
            values = [
                result["group"],
                result["n"],
                f"{result['statistic']:.4f}",
                f"{result['p_value']:.4f}",
                "Yes" if result["is_normal"] else "No",
            ]

            item_id = self.trees["normality"].insert("", "end", values=values)

            if not result["is_normal"]:
                self.trees["normality"].item(item_id, tags=("not_normal",))

        # Configure the tag
        self.trees["normality"].tag_configure("not_normal", background="#ffcccc")

        # Store results for export
        self.current_results["normality"] = results

        messagebox.showinfo(
            "Normality Test", f"Completed normality testing for {len(results)} groups"
        )

    def _run_assumption_tests(self):
        """Run assumption tests"""
        metric_type = self.assumption_vars["metric_type"].get()
        variable = self.assumption_vars["variable"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Clear the treeview
        for item in self.trees["assumption"].get_children():
            self.trees["assumption"].delete(item)

        results = []

        # Run selected tests
        if self.assumption_vars["test_homogeneity"].get():
            # Test for each factor
            for factor in ["Condition", "Timepoint"]:
                if factor in df.columns:
                    result = self.stats_service.test_homogeneity_levene(df, factor)
                    results.append(result)

        if self.assumption_vars["test_sphericity"].get():
            result = self.stats_service.test_sphericity_mauchly(df)
            results.append(result)

        if self.assumption_vars["test_heteroscedasticity"].get():
            result = self.stats_service.test_heteroscedasticity_breusch_pagan(df)
            results.append(result)

        # Populate treeview
        for result in results:
            if "error" not in result:
                values = [
                    result["test"],
                    (
                        f"{result['statistic']:.4f}"
                        if not pd.isna(result["statistic"])
                        else "N/A"
                    ),
                    (
                        f"{result['p_value']:.4f}"
                        if not pd.isna(result["p_value"])
                        else "N/A"
                    ),
                    "Yes" if result["assumption_met"] else "No",
                ]

                item_id = self.trees["assumption"].insert("", "end", values=values)

                if not result["assumption_met"]:
                    self.trees["assumption"].item(item_id, tags=("failed",))

        # Configure the tag
        self.trees["assumption"].tag_configure("failed", background="#ffcccc")

        # Store results for export
        self.current_results["assumption"] = results

        messagebox.showinfo(
            "Assumption Tests", f"Completed {len(results)} assumption tests"
        )

    def _run_anova(self):
        """Run ANOVA analysis"""
        metric_type = self.anova_vars["metric_type"].get()
        variable = self.anova_vars["variable"].get()
        anova_type = self.anova_vars["type"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Get selected factors
        factors = []
        if self.anova_vars["factor_condition"].get():
            factors.append("Condition")
        if self.anova_vars["factor_timepoint"].get():
            factors.append("Timepoint")

        if not factors:
            messagebox.showwarning("No Factors", "Please select at least one factor")
            return

        # Clear the treeview
        for item in self.trees["anova"].get_children():
            self.trees["anova"].delete(item)

        # Run ANOVA
        include_interaction = (
            self.anova_vars["factor_interaction"].get() and len(factors) >= 2
        )
        results = self.stats_service.run_anova(
            df, anova_type, factors, include_interaction
        )

        if "error" in results:
            messagebox.showerror(
                "ANOVA Error", f"Error running ANOVA: {results['error']}"
            )
            return

        # Populate treeview
        if results["anova_table"] is not None:
            anova_table = results["anova_table"]
            for index, row in anova_table.iterrows():
                values = [
                    index,  # Source
                    f"{row['sum_sq']:.4f}",  # Sum of Squares
                    f"{row['df']:.0f}",  # df
                    (
                        f"{row['sum_sq']/row['df']:.4f}" if row["df"] > 0 else "N/A"
                    ),  # Mean Square
                    f"{row['F']:.4f}" if not pd.isna(row["F"]) else "N/A",  # F
                    (
                        f"{row['PR(>F)']:.4f}" if not pd.isna(row["PR(>F)"]) else "N/A"
                    ),  # p-value
                    (
                        f"{row['partial_eta_sq']:.4f}"
                        if "partial_eta_sq" in row
                        and not pd.isna(row["partial_eta_sq"])
                        else "N/A"
                    ),  # Partial η²
                    "N/A",  # Observed Power (not implemented)
                ]

                item_id = self.trees["anova"].insert("", "end", values=values)

                # Highlight significant results
                if (
                    "PR(>F)" in row
                    and not pd.isna(row["PR(>F)"])
                    and row["PR(>F)"] < 0.05
                ):
                    self.trees["anova"].item(item_id, tags=("significant",))

        # Configure the tag
        self.trees["anova"].tag_configure("significant", background="#ccffcc")

        # Store results for export
        self.current_results["anova"] = results

        messagebox.showinfo(
            "ANOVA Complete",
            f"ANOVA completed\nR² = {results.get('r_squared', 'N/A'):.4f}"
            f"\nAdjusted R² = {results.get('adj_r_squared', 'N/A'):.4f}",
        )

    def _run_posthoc_test(self):
        """Run post-hoc tests"""
        metric_type = self.posthoc_vars["metric_type"].get()
        variable = self.posthoc_vars["variable"].get()
        test_type = self.posthoc_vars["test"].get()
        factor = self.posthoc_vars["factor"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Clear the treeview
        for item in self.trees["posthoc"].get_children():
            self.trees["posthoc"].delete(item)

        # Run post-hoc test
        results = self.stats_service.run_posthoc_test(df, factor, test_type)

        # Populate treeview
        for result in results:
            if "error" not in result:
                values = [
                    str(result["group1"]),
                    str(result["group2"]),
                    f"{result['mean_diff']:.4f}",
                    (
                        f"{result['std_error']:.4f}"
                        if "std_error" in result and not pd.isna(result["std_error"])
                        else "N/A"
                    ),
                    (
                        f"{result.get('t_value', 'N/A'):.4f}"
                        if "t_value" in result and not pd.isna(result.get("t_value"))
                        else "N/A"
                    ),
                    f"{result['p_value']:.4f}",
                    result["significant"],
                ]

                item_id = self.trees["posthoc"].insert("", "end", values=values)

                if result["significant"] == "Yes":
                    self.trees["posthoc"].item(item_id, tags=("significant",))

        # Configure the tag
        self.trees["posthoc"].tag_configure("significant", background="#ccffcc")

        # Store results for export
        self.current_results["posthoc"] = results

        messagebox.showinfo(
            "Post-hoc Test Complete", f"Completed {len(results)} pairwise comparisons"
        )

    def _run_paired_tests(self):
        """Run paired t-test or Wilcoxon signed-rank test"""
        metric_type = self.paired_test_vars["metric_type"].get()
        variable = self.paired_test_vars["variable"].get()
        test_type = self.paired_test_vars["test_type"].get()
        group_factor = self.paired_test_vars["group_factor"].get()

        if not variable:
            messagebox.showwarning("No Variable", "Please select a variable to analyze")
            return

        # Extract data
        df = self.stats_service.extract_data_for_analysis(
            self.analyzer, metric_type, variable
        )
        if df is None:
            messagebox.showwarning(
                "No Data", "No data available for the selected variable"
            )
            return

        # Clear the treeview
        for item in self.trees["paired_test"].get_children():
            self.trees["paired_test"].delete(item)

        # Run paired tests
        results = self.stats_service.run_paired_tests(df, test_type, group_factor)

        # Populate treeview
        for result in results:
            if "error" not in result:
                # Format results based on test type
                if test_type == "paired_t":
                    values = [
                        result["comparison"],
                        result["test_type"],
                        str(result["n_pairs"]),
                        f"t = {result['t_statistic']:.3f}",
                        f"{result['p_value']:.4f}",
                        f"{result['effect_size']} (d = {result['cohens_d']:.3f})",
                        f"{result['ci_lower']:.3f}",
                        f"{result['ci_upper']:.3f}",
                        result["significant"],
                    ]
                else:  # wilcoxon
                    values = [
                        result["comparison"],
                        result["test_type"],
                        str(result["n_pairs"]),
                        f"W = {result['w_statistic']:.1f}",
                        f"{result['p_value']:.4f}",
                        f"{result['effect_size']} (r = {result['r_effect_size']:.3f})",
                        "N/A",  # CI not available for Wilcoxon
                        "N/A",
                        result["significant"],
                    ]

                item_id = self.trees["paired_test"].insert("", "end", values=values)

                if result["significant"] == "Yes":
                    self.trees["paired_test"].item(item_id, tags=("significant",))
            else:
                # Handle errors
                error_values = [
                    result.get("comparison", "Error"),
                    result.get("test_type", "Error"),
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    result["error"],
                ]
                item_id = self.trees["paired_test"].insert(
                    "", "end", values=error_values
                )
                self.trees["paired_test"].item(item_id, tags=("error",))

        # Configure the tags
        self.trees["paired_test"].tag_configure("significant", background="#ccffcc")
        self.trees["paired_test"].tag_configure("error", background="#ffcccc")

        # Store results for export
        self.current_results["paired_test"] = results

        # Show summary
        valid_results = [r for r in results if "error" not in r]
        error_results = [r for r in results if "error" in r]

        test_name = (
            "Paired t-test" if test_type == "paired_t" else "Wilcoxon signed-rank test"
        )
        message = f"Completed {test_name}\n\n"

        if valid_results:
            message += f"• {len(valid_results)} valid comparisons\n"
            significant = sum(1 for r in valid_results if r["significant"] == "Yes")
            message += f"• {significant} significant results\n"

        if error_results:
            message += f"• {len(error_results)} errors occurred\n"

        messagebox.showinfo("Paired Tests Complete", message)

    # Export methods
    def _export_outlier_results(self):
        """Export outlier detection results"""
        self._export_results("outlier", "Outlier_Detection_Results")

    def _export_normality_results(self):
        """Export normality test results"""
        self._export_results("normality", "Normality_Test_Results")

    def _export_assumption_results(self):
        """Export assumption test results"""
        self._export_results("assumption", "Assumption_Test_Results")

    def _export_anova_results(self):
        """Export ANOVA results"""
        self._export_results("anova", "ANOVA_Results")

    def _export_posthoc_results(self):
        """Export post-hoc test results"""
        self._export_results("posthoc", "PostHoc_Test_Results")

    def _export_paired_test_results(self):
        """Export paired test results"""
        self._export_results("paired_test", "Paired_Test_Results")

    def _export_results(self, result_type: str, default_filename: str):
        """Generic export method for results - exports what's currently displayed in the treeview"""
        if result_type not in self.trees:
            messagebox.showwarning("No Results", f"No {result_type} results to export")
            return

        tree = self.trees[result_type]

        # Check if there's any data in the treeview
        if not tree.get_children():
            messagebox.showwarning("No Data", "No data available to export")
            return

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{default_filename}.csv",
        )

        if not filename:
            return

        try:
            # Get column headers
            columns = [tree.heading(col)["text"] for col in tree["columns"]]

            # Get all data from treeview
            data_rows = []
            for item in tree.get_children():
                values = tree.item(item)["values"]
                data_rows.append(values)

            # Create DataFrame and export
            df = pd.DataFrame(data_rows, columns=columns)
            df.to_csv(filename, index=False)

            # Add metadata for ANOVA results if available
            if result_type == "anova" and "anova" in self.current_results:
                anova_results = self.current_results["anova"]
                if "r_squared" in anova_results:
                    # Append model summary to the file
                    with open(filename, "a", newline="") as f:
                        f.write(f"\n\nModel Summary:\n")
                        f.write(
                            f"R-squared,{anova_results.get('r_squared', 'N/A'):.4f}\n"
                        )
                        f.write(
                            f"Adjusted R-squared,{anova_results.get('adj_r_squared', 'N/A'):.4f}\n"
                        )
                        f.write(f"Formula,{anova_results.get('formula', 'N/A')}\n")

            messagebox.showinfo("Export Complete", f"Results exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")


def get_statistics_gui_service(parent_window, analyzer) -> StatisticsGUIService:
    """Create a new statistics GUI service instance"""
    return StatisticsGUIService(parent_window, analyzer)
