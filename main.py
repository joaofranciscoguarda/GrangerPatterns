import os
import sys
from pathlib import Path
import pandas as pd
import argparse
from granger_analysis import GrangerCausalityAnalyzer
from visualize_matrix import plot_connectivity_matrix
from visualize_network import plot_network_graph
from visualize_nodal import plot_nodal_metrics
from visualize_pairwise import plot_pairwise_comparison
from visualize_global import plot_global_metrics
import report_generator

def create_directories():
    """Create necessary directories"""
    os.makedirs('output/figures', exist_ok=True)
    os.makedirs('output/reports', exist_ok=True)
    os.makedirs('output/tables', exist_ok=True)

def main():
    """Main function to run the Granger Causality analysis"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze Granger Causality from Excel files")
    parser.add_argument('-d', '--data_dir', default='data', help='Directory containing Excel files')
    parser.add_argument('-o', '--output_dir', default='output', help='Output directory')
    parser.add_argument('-f', '--file', help='Specific Excel file to analyze')
    parser.add_argument('-c', '--condition', help='Filter by condition')
    parser.add_argument('-t', '--timepoint', help='Filter by timepoint')
    parser.add_argument('-g', '--gui', action='store_true', help='Launch graphical user interface')
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        try:
            import tkinter as tk
            from gui import GrangerCausalityAnalyzerGUI
            
            root = tk.Tk()
            app = GrangerCausalityAnalyzerGUI(root)
            root.mainloop()
            return
        except ImportError:
            print("Tkinter is not available. Please install tkinter to use the GUI.")
            return
    
    # Create directories
    create_directories()
    
    # Initialize the analyzer
    analyzer = GrangerCausalityAnalyzer()
    
    # Load data
    if args.file:
        if os.path.exists(args.file):
            print(f"Loading file: {args.file}")
            analyzer.load_data(args.file)
        else:
            print(f"File not found: {args.file}")
            return
    else:
        print(f"Loading files from directory: {args.data_dir}")
        analyzer.load_multiple_files(directory_path=args.data_dir)
    
    # Check if data was loaded
    if not analyzer.processed_data:
        print("No data was loaded. Please check your file paths.")
        return
    
    # Run analysis
    print("Running analysis...")
    analyzer.analyze_all_data()
    
    # Generate visualizations and reports for each analysis
    print("Generating visualizations and reports...")
    for key, analysis in analyzer.analyses.items():
        participant_id = analysis['metadata']['participant_id']
        timepoint = analysis['metadata']['timepoint']
        condition = analysis['metadata']['condition']
        
        base_name = f"{participant_id}_{timepoint}_{condition}"
        print(f"Processing: {base_name}")
        
        # Create output paths
        figures_dir = os.path.join(args.output_dir, 'figures')
        reports_dir = os.path.join(args.output_dir, 'reports')
        tables_dir = os.path.join(args.output_dir, 'tables')
        
        # Generate visualizations
        print("  - Creating matrix visualization")
        plot_connectivity_matrix(
            analysis['connectivity_matrix'], 
            f"Granger Causality Matrix: {participant_id} {timepoint} {condition}", 
            os.path.join(figures_dir, f"{base_name}_matrix.png")
        )
        
        print("  - Creating network visualization")
        G = analyzer.create_network_graph(key)
        plot_network_graph(
            G, 
            f"Granger Causality Network: {participant_id} {timepoint} {condition}", 
            os.path.join(figures_dir, f"{base_name}_network.png")
        )
        
        print("  - Creating nodal metrics visualization")
        plot_nodal_metrics(
            analysis['nodal'], 
            f"Nodal Metrics: {participant_id} {timepoint} {condition}", 
            os.path.join(figures_dir, f"{base_name}_nodal.png")
        )
        
        print("  - Creating pairwise comparison visualization")
        plot_pairwise_comparison(
            analysis['pairwise'], 
            f"Pairwise Connections: {participant_id} {timepoint} {condition}", 
            os.path.join(figures_dir, f"{base_name}_pairwise.png")
        )
        
        print("  - Creating global metrics visualization")
        plot_global_metrics(
            analysis['global'], 
            f"Global Metrics: {participant_id} {timepoint} {condition}", 
            os.path.join(figures_dir, f"{base_name}_global.png")
        )
        
        # Generate report
        print("  - Generating report")
        report_path = os.path.join(reports_dir, f"{base_name}_report.pdf")
        report_generator.generate_report(analysis, report_path, figures_dir, base_name)
        
        # Generate tables
        print("  - Generating data tables")
        # Nodal metrics table
        nodal_df = pd.DataFrame({
            'Participant': participant_id,
            'Condition': condition,
            'Timepoint': timepoint,
            'Electrode': list(analysis['nodal'].keys()),
            'In-Strength': [m['in_strength'] for m in analysis['nodal'].values()],
            'Out-Strength': [m['out_strength'] for m in analysis['nodal'].values()],
            'Causal Flow': [m['causal_flow'] for m in analysis['nodal'].values()],
            'Category': [m['category'] for m in analysis['nodal'].values()]
        })
        nodal_df.to_csv(os.path.join(tables_dir, f"{base_name}_nodal.csv"), index=False)
        
        # Global metrics table
        global_df = pd.DataFrame({
            'Participant': [participant_id],
            'Condition': [condition],
            'Timepoint': [timepoint],
            'Global GC Strength': [analysis['global']['global_gc_strength']],
            'Mean GC Strength': [analysis['global']['mean_gc_strength']],
            'Network Density (th=0.0001)': [analysis['global']['network_density_th0.0001']],
            'Network Density (th=0.0005)': [analysis['global']['network_density_th0.0005']],
            'Network Density (th=0.001)': [analysis['global']['network_density_th0.001']]
        })
        global_df.to_csv(os.path.join(tables_dir, f"{base_name}_global.csv"), index=False)
        
        # Pairwise connections table
        pairwise_rows = []
        for pair, value in analysis['pairwise']['directional_pairs'].items():
            source, target = pair.split('→')
            pairwise_rows.append({
                'Participant': participant_id,
                'Condition': condition,
                'Timepoint': timepoint,
                'Source': source,
                'Target': target,
                'GC Value': value
            })
        pairwise_df = pd.DataFrame(pairwise_rows)
        pairwise_df.to_csv(os.path.join(tables_dir, f"{base_name}_pairwise.csv"), index=False)
    
    # Generate group statistics if multiple files
    if len(analyzer.analyses) > 1:
        print("Generating group statistics...")
        
        # Filter by condition and timepoint if specified
        group_stats = analyzer.get_group_statistics(
            filter_condition=args.condition,
            filter_timepoint=args.timepoint
        )
        
        if "error" in group_stats:
            print(f"Error generating group statistics: {group_stats['error']}")
        else:
            # Name for group files
            if args.condition and args.timepoint:
                group_name = f"group_{args.condition}_{args.timepoint}"
            elif args.condition:
                group_name = f"group_{args.condition}"
            elif args.timepoint:
                group_name = f"group_{args.timepoint}"
            else:
                group_name = "group_all"
            
            # Generate group report
            print(f"  - Generating group report: {group_name}")
            report_path = os.path.join(reports_dir, f"{group_name}_report.pdf")
            report_generator.generate_group_report(group_stats, report_path, figures_dir, group_name)
            
            # Generate group tables
            print(f"  - Generating group data tables: {group_name}")
            
            # Nodal metrics table
            nodal_rows = []
            for electrode, metrics in group_stats['nodal'].items():
                nodal_rows.append({
                    'Electrode': electrode,
                    'In-Strength (Mean)': metrics['in_strength_mean'],
                    'In-Strength (SD)': metrics['in_strength_std'],
                    'Out-Strength (Mean)': metrics['out_strength_mean'],
                    'Out-Strength (SD)': metrics['out_strength_std'],
                    'Causal Flow (Mean)': metrics['causal_flow_mean'],
                    'Causal Flow (SD)': metrics['causal_flow_std'],
                    'Dominant Category': metrics['dominant_category']
                })
            nodal_df = pd.DataFrame(nodal_rows)
            nodal_df.to_csv(os.path.join(tables_dir, f"{group_name}_nodal.csv"), index=False)
            
            # Global metrics table
            global_rows = []
            for metric, values in group_stats['global'].items():
                global_rows.append({
                    'Metric': metric,
                    'Mean': values['mean'],
                    'SD': values['std'],
                    'Min': values['min'],
                    'Max': values['max']
                })
            global_df = pd.DataFrame(global_rows)
            global_df.to_csv(os.path.join(tables_dir, f"{group_name}_global.csv"), index=False)
            
            # Pairwise connections table
            pairwise_rows = []
            for pair, values in group_stats['pairwise'].items():
                source, target = pair.split('→')
                pairwise_rows.append({
                    'Source': source,
                    'Target': target,
                    'Mean GC Value': values['mean'],
                    'SD GC Value': values['std']
                })
            pairwise_df = pd.DataFrame(pairwise_rows)
            pairwise_df.to_csv(os.path.join(tables_dir, f"{group_name}_pairwise.csv"), index=False)
    
    print("Analysis complete!")

if __name__ == "__main__":
    main() 