Developed by Dr. Marcelo Bigliassi (Florida International University, USA)

# GrangerPatterns

GrangerPatterns is a comprehensive graphical interface for analyzing Granger causality in neural data, with particular emphasis on EEG connectivity patterns. The application provides tools for data loading, analysis, visualization, and statistical testing.

## Features

- **Data Management**: Easy file import with metadata tagging (participant ID, condition, timepoint)
- **Granger Causality Analysis**: Analyze directed connectivity between signals
- **Network Metrics**: Calculate global network metrics, nodal metrics, and pairwise connections
- **Visualization**: Generate various visualizations:
  - Connectivity matrices
  - Network graphs
  - Nodal metrics plots
  - Global metrics charts
  - Pairwise connection comparisons
- **Statistical Analysis**: Comprehensive statistical tools:
  - Outlier detection and handling
  - Normality tests (Shapiro-Wilk)
  - ANOVA (repeated measures, factorial, mixed designs)
  - Post-hoc tests (Bonferroni, Tukey HSD)
  - Effect size calculation (partial eta-squared)
  - Observed power estimation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YourUsername/GrangerPatterns.git
cd GrangerPatterns
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

If requirements.txt is not available, install the following packages:
```bash
pip install numpy pandas scipy matplotlib seaborn networkx pingouin tkinter statsmodels
```

## Usage

1. Run the application:
```bash
python src/gui.py
```

2. **File Selection**: Use the "Add Files" button to select your data files (CSV or Excel)

3. **Metadata Assignment**: Double-click on files to assign participant ID, condition, and timepoint

4. **Analysis**:
   - Click "Load Data" to load selected files
   - Click "Analyze All" to perform Granger causality analysis
   - Click "Generate Tables" to create tabular outputs of results

5. **Visualization**:
   - Select a metric type (Global, Nodal, Network, Pairwise, Matrix, or All)
   - Click "Generate Visualization" to create visualizations
   - Select an output directory for results

6. **Statistical Analysis**:
   - Click "Open Statistics Window" to access statistical tools
   - Navigate between tabs for different statistical tests:
     - Outlier Detection
     - Normality Tests
     - Assumption Tests
     - ANOVA
     - Post-hoc Tests

## Statistical Analysis Guide

### Outlier Detection
- Select a metric and variable
- Choose detection method (Z-Score or IQR)
- Identify and optionally remove outliers

### Normality Tests
- Run Shapiro-Wilk tests to check data normality
- Group data by condition, timepoint, or both

### ANOVA
- Run different types of ANOVA designs:
  - Factorial ANOVA (between-subjects)
  - Repeated Measures ANOVA (within-subjects)
  - Mixed ANOVA (between-within design)
- Include factors: Timepoint, Condition, Group
- View results with effect sizes and observed power

### Post-hoc Tests
- Run Bonferroni or Tukey HSD tests
- Compare groups based on condition, timepoint, or their interaction

## Data Format

The application accepts CSV and Excel files with the following expected format:
- Time series data with each column representing a different signal/electrode
- Column headers should be meaningful labels for the signals

## Contributor

- Dr. Marcelo Bigliassi

## License

This project is licensed under the [MIT License](LICENSE). 
