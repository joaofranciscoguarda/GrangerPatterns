# Unified Batch Processor for Granger Causality Analysis

## Overview

The `batch_processor.py` is a unified, high-performance script that consolidates all Granger Causality analysis types into a single, memory-efficient interface. It provides concurrent execution of multiple analysis types while preventing memory overflow through controlled concurrency.

## Features

### 🚀 **Concurrent Processing**

- **Memory-Safe**: Uses asyncio with semaphores to limit concurrent processes
- **Configurable Concurrency**: Adjust `--concurrent` parameter based on your machine's capabilities
- **Async Execution**: All analyses run asynchronously for optimal performance

### 🎯 **Flexible Analysis Selection**

- **All-in-One**: Run all 5 analysis types with `--all`
- **Selective**: Choose specific analyses (e.g., `--matrix --network`)
- **Custom Combinations**: Mix and match any analysis types

### 📁 **Smart Directory Management**

- **Custom Input/Output**: Specify custom directories with `--input` and `--output`
- **Auto-Creation**: Output directories are created automatically
- **Validation**: Input directory existence is verified before processing

### 📊 **Comprehensive Reporting**

- **Real-time Progress**: Live updates during execution
- **Detailed Results**: Success/failure status for each analysis
- **Performance Metrics**: Execution time for each process
- **Error Handling**: Clear error reporting with stack traces

## Analysis Types

| Analysis           | Flag               | Description                                                | Output             |
| ------------------ | ------------------ | ---------------------------------------------------------- | ------------------ |
| **Matrix**         | `--matrix`         | Connectivity matrix heatmaps with consistent scaling       | `output/matrices/` |
| **Network**        | `--network`        | Network graph visualizations with consistent scaling       | `output/networks/` |
| **Nodal**          | `--nodal`          | Nodal metric bar charts with consistent scaling            | `output/nodals/`   |
| **Pairwise**       | `--pairwise`       | Pairwise connection strength plots with consistent scaling | `output/pairwise/` |
| **Global Metrics** | `--global-metrics` | Global metric bar charts with consistent scaling           | `output/global/`   |

## Installation & Setup

### Prerequisites

```bash
# Activate your virtual environment
source venv/bin/activate

# Ensure all dependencies are installed
pip install -r requirements.txt
```

### File Structure

```
GrangerPatterns/
├── batch_processor.py           # Main unified script
├── batch_matrix_processor.py    # Matrix analysis module
├── batch_network_processor.py   # Network analysis module
├── batch_nodal_processor.py     # Nodal analysis module
├── batch_pairwise_processor.py  # Pairwise analysis module
├── batch_global_processor.py    # Global metrics module
├── services/                    # Shared service modules
├── input/                       # Excel files to process
└── output/                      # Generated visualizations
```

## Usage

### Basic Commands

#### Run All Analyses

```bash
python batch_processor.py --all
```

#### Run Specific Analyses

```bash
# Matrix and network only
python batch_processor.py --matrix --network

# Nodal and global metrics
python batch_processor.py --nodal --global-metrics

# Single analysis
python batch_processor.py --matrix
```

#### Custom Directories

```bash
python batch_processor.py --all --input custom_input --output custom_output
```

#### Adjust Concurrency

```bash
# Allow 4 concurrent processes (if you have sufficient RAM)
python batch_processor.py --all --concurrent 4

# Conservative approach (default: 2)
python batch_processor.py --all --concurrent 2
```

### Command-Line Options

```bash
python batch_processor.py [OPTIONS]

Options:
  --all                    Run all analysis types
  --matrix                 Run matrix visualizations
  --network                Run network visualizations
  --nodal                  Run nodal visualizations
  --pairwise               Run pairwise visualizations
  --global-metrics         Run global metrics visualizations

  --input INPUT            Input directory (default: input)
  --output OUTPUT          Output directory (default: output)
  --concurrent N           Max concurrent processes (default: 2)

  -h, --help              Show help message
```

## Examples

### Example 1: Quick Matrix Analysis

```bash
python batch_processor.py --matrix
```

**Output**: Generates matrix visualizations in `output/matrices/`

### Example 2: Network and Nodal Analysis

```bash
python batch_processor.py --network --nodal
```

**Output**: Generates both network and nodal visualizations concurrently

### Example 3: Full Pipeline with High Performance

```bash
python batch_processor.py --all --concurrent 4 --output results_$(date +%Y%m%d)
```

**Output**: Runs all analyses with 4 concurrent processes, saves to timestamped directory

### Example 4: Custom Analysis Pipeline

```bash
python batch_processor.py --matrix --network --global-metrics --input data_2024 --output analysis_results
```

**Output**: Runs matrix, network, and global metrics on custom directories

## Architecture

### **Modular Design**

Each analysis type is implemented as a separate module with a standardized interface:

```python
# Each processor exports a main function
async def process_matrix_analysis(input_dir="input", output_dir="output"):
    # Matrix-specific logic
    return success_status

async def process_network_analysis(input_dir="input", output_dir="output"):
    # Network-specific logic
    return success_status
```

### **Concurrent Execution**

The unified processor orchestrates multiple analyses:

```python
# Create controlled concurrent tasks
semaphore = asyncio.Semaphore(max_concurrent)
tasks = [
    run_analysis(analysis_type, input_dir, output_dir, semaphore)
    for analysis_type in selected_types
]

# Execute all concurrently
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### **Memory Management**

- **Semaphore Control**: Limits active processes to prevent memory overflow
- **Async I/O**: Non-blocking operations for efficient resource usage
- **Configurable Limits**: Adjust concurrency based on available RAM

## Performance Considerations

### **Concurrency Settings**

| Machine Specs | Recommended Setting | Notes                                   |
| ------------- | ------------------- | --------------------------------------- |
| **4GB RAM**   | `--concurrent 1`    | Conservative, safe for all machines     |
| **8GB RAM**   | `--concurrent 2`    | Default setting, balanced performance   |
| **16GB RAM**  | `--concurrent 3`    | Good performance, moderate memory usage |
| **32GB+ RAM** | `--concurrent 4`    | High performance, ensure sufficient RAM |

### **Memory Usage Patterns**

- **Matrix Analysis**: Moderate memory usage, good for concurrent execution
- **Network Analysis**: Higher memory usage, benefits from controlled concurrency
- **Nodal Analysis**: Low memory usage, excellent for concurrent execution
- **Pairwise Analysis**: Moderate memory usage, good for concurrent execution
- **Global Metrics**: Low memory usage, excellent for concurrent execution

## Output Structure

```
output/
├── matrices/              # Matrix visualizations
│   ├── individual/        # Per-participant matrices
│   └── by_condition/      # Condition-averaged matrices
├── networks/              # Network visualizations
│   ├── individual/        # Per-participant networks
│   └── by_condition/      # Condition-averaged networks
├── nodals/                # Nodal metric visualizations
│   ├── individual/        # Per-participant nodal plots
│   └── by_condition/      # Condition-averaged nodal plots
├── pairwise/              # Pairwise connection plots
│   ├── individual/        # Per-participant pairwise plots
│   └── by_condition/      # Condition-averaged pairwise plots
├── global/                # Global metrics visualizations
│   ├── individual/        # Per-participant global plots
│   └── by_condition/      # Condition-averaged global plots
└── reports/               # Analysis summary reports
```

## Error Handling

### **Graceful Failures**

- Individual analysis failures don't stop other analyses
- Detailed error reporting with stack traces
- Clear success/failure summary at the end

### **Common Issues & Solutions**

#### **Memory Errors**

```bash
# Reduce concurrency
python batch_processor.py --all --concurrent 1
```

#### **File Permission Errors**

```bash
# Check directory permissions
ls -la input/ output/
chmod 755 input/ output/
```

#### **Import Errors**

```bash
# Ensure virtual environment is activated
source venv/bin/activate
python batch_processor.py --help
```

## Integration with Existing Workflow

### **Standalone Usage**

Each individual processor can still be run independently:

```bash
python batch_matrix_processor.py      # Matrix only
python batch_network_processor.py     # Network only
python batch_nodal_processor.py       # Nodal only
```

### **GUI Integration**

The unified processor can be integrated into GUI workflows:

```python
# Example: Run from Python code
import asyncio
from batch_processor import run_analyses

async def run_gui_analysis():
    results = await run_analyses(
        ["matrix", "network"],
        "input",
        "output",
        max_concurrent=2
    )
    return results
```

## Troubleshooting

### **Performance Issues**

- **Slow Execution**: Increase `--concurrent` value
- **Memory Errors**: Decrease `--concurrent` value
- **Disk Space**: Ensure sufficient space in output directory

### **Analysis Failures**

- **Check Logs**: Review error messages in terminal output
- **Verify Input**: Ensure Excel files are valid and accessible
- **Dependencies**: Confirm all required packages are installed

### **Caching Issues**

- **Database Reset**: Delete `cache.db` to clear cached results
- **File Changes**: Ensure input files haven't been modified since last run

## Future Enhancements

### **Planned Features**

- **Progress Bars**: Visual progress indicators for long-running analyses
- **Resume Capability**: Resume interrupted analysis runs
- **Batch Configuration**: YAML/JSON configuration files for complex workflows
- **Cloud Integration**: Support for cloud-based processing

### **Extensibility**

The modular architecture makes it easy to add new analysis types:

1. Create new processor module
2. Export `process_*_analysis()` function
3. Add to `ANALYSIS_TYPES` dictionary
4. Update documentation

## Support & Contributing

### **Getting Help**

- Check this README for common issues
- Review terminal output for error messages
- Ensure all dependencies are properly installed

### **Contributing**

- Follow the existing code structure
- Maintain async function signatures
- Add comprehensive error handling
- Update this README for new features

---

**Note**: This unified processor maintains 100% compatibility with individual processor scripts while providing significant performance and usability improvements through concurrent execution and memory management.
