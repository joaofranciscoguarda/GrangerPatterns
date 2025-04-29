# Granger Causality Analysis Tool

A comprehensive tool for analyzing and visualizing Granger Causality data from EEG electrodes.

## Overview

This tool analyzes Granger Causality (GC) matrices from Excel files to extract key connectivity metrics:

1. **Directional Connectivity Strengths**: Pairwise GC values showing directional influence between electrodes
2. **Electrode-Level Metrics**: In-strength, out-strength, and causal flow metrics per electrode
3. **Global Measures**: Overall network connectivity and density metrics

The tool generates publication-quality visualizations and comprehensive PDF reports explaining all results. It includes both a command-line interface and a graphical user interface (GUI) for easy data management and analysis.

## Features

- Load and process GC matrices from Excel files
- Calculate multiple connectivity metrics at different levels of analysis
- Generate publication-ready visualizations:
  - Connectivity matrices as heatmaps
  - Network graphs showing directional connectivity
  - Bar charts for nodal metrics and pairwise comparisons
- Generate comprehensive PDF reports with explanations
- Group-level analysis for multiple participants and conditions
- User-friendly GUI with:
  - File management with metadata editing
  - One-click analysis and visualization
  - Statistical analysis tools
- Statistical analysis capabilities:
  - Outlier detection (Z-score and IQR methods)
  - Normality testing (Shapiro-Wilk)
  - ANOVA assumption testing (Levene's test, Breusch-Pagan)
  - Factorial ANOVA (condition, timepoint, interaction effects)
  - Post-hoc tests (Bonferroni, Tukey HSD)
  - Effect size calculation (partial eta squared)
  - Observed power analysis

## Directory Structure

```
├── data/               # Input Excel files with GC matrices
├── output/             # Output directory
│   ├── figures/        # Generated visualizations
│   └── reports/        # Generated PDF reports
└── src/                # Source code
    ├── granger_analysis.py    # Core analysis functions
    ├── main.py                # CLI entry point
    ├── gui.py                 # GUI application
    ├── report_generator.py    # Report generation
    ├── visualize_*.py         # Visualization modules
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

### GUI Usage

To launch the graphical user interface:

```bash
python src/gui.py
```

The GUI provides:
- File management for adding and editing data files
- Analysis options for processing data
- Visualization tools for generating plots
- Statistical analysis with interactive result displays

### Command-Line Usage

```bash
python src/main.py
```

This will process all Excel files in the `data/` directory.

### Options

```bash
# Process a specific file
python src/main.py --file data/my_file.xlsx

# Set custom input/output directories
python src/main.py --data_dir my_data --output_dir my_output

# Filter by condition or timepoint for group analysis
python src/main.py --condition Phase1 --timepoint T2

# Launch GUI
python src/main.py --gui
```

### File Naming Convention

Excel files should follow the naming convention: `UTF-[ID]_T[timepoint]_[condition].xlsx`

Example: `UTF-8002_T2_Phase1.xlsx`

## Input Data Format

The Excel files should contain a matrix where:
- First column contains electrode names (sources)
- First row contains electrode names (targets)
- Each cell contains the GC value from source (row) to target (column)

## Output

The tool generates:
1. Visualization files in PNG format
2. Individual PDF reports for each analysis
3. Group-level reports when multiple files are analyzed
4. Statistical analysis reports and tables

## Statistical Analysis

The statistical analysis module provides:

1. **Outlier Detection**:
   - Z-Score method (±3 standard deviations)
   - IQR method (1.5 × interquartile range)
   - Outlier visualization and export capabilities

2. **Normality Testing**:
   - Shapiro-Wilk test
   - Group-based normality assessment (condition, timepoint, or both)

3. **Assumption Testing**:
   - Homogeneity of variance (Levene's test)
   - Heteroscedasticity (Breusch-Pagan test)

4. **ANOVA**:
   - Factorial ANOVA with condition and timepoint factors
   - Support for interaction effects
   - Effect size calculation (partial eta squared)
   - Observed power calculation

5. **Post-hoc Tests**:
   - Bonferroni correction
   - Tukey HSD
   - Pairwise comparison tables

## License

MIT 