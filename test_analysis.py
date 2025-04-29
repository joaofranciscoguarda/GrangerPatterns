import os
import sys
from pathlib import Path
from granger_analysis import GrangerCausalityAnalyzer
from visualize_matrix import plot_connectivity_matrix
from visualize_network import plot_network_graph
from visualize_nodal import plot_nodal_metrics
from visualize_pairwise import plot_pairwise_comparison
from visualize_global import plot_global_metrics

def test_analysis():
    """Run a test analysis on a sample file"""
    # Create output directories
    os.makedirs('output/figures', exist_ok=True)
    os.makedirs('output/reports', exist_ok=True)
    
    # Sample file path
    sample_file = os.path.join('data', 'UTF-8002_T2_Phase1.xlsx')
    
    if not os.path.exists(sample_file):
        print(f"Error: Sample file {sample_file} not found.")
        return
    
    print(f"Testing analysis on {sample_file}...")
    
    # Initialize analyzer
    analyzer = GrangerCausalityAnalyzer()
    
    # Load data
    print("Loading data...")
    analyzer.load_data(sample_file)
    
    # Run analysis
    print("Running analysis...")
    analyzer.analyze_all_data()
    
    # Get the analysis results
    analysis_key = next(iter(analyzer.analyses.keys()))
    analysis = analyzer.analyses[analysis_key]
    
    # Print basic information
    participant_id = analysis['metadata']['participant_id']
    timepoint = analysis['metadata']['timepoint']
    condition = analysis['metadata']['condition']
    
    print(f"\nAnalysis for: Participant {participant_id}, {timepoint}, {condition}")
    
    # Print nodal categories
    print("\nElectrode categories:")
    for electrode, metrics in analysis['nodal'].items():
        print(f"  {electrode}: {metrics['category']} (Causal Flow: {metrics['causal_flow']:.6f})")
    
    # Print global metrics
    print("\nGlobal metrics:")
    print(f"  Global GC strength: {analysis['global']['global_gc_strength']:.6f}")
    print(f"  Mean GC strength: {analysis['global']['mean_gc_strength']:.6f}")
    print(f"  Network density (th=0.0005): {analysis['global']['network_density_th0.0005']:.6f}")
    
    # Test creating a network graph
    print("\nCreating network graph...")
    G = analyzer.create_network_graph(analysis_key)
    print(f"  Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Test generating figures
    print("\nGenerating test figures...")
    figures_dir = 'output/figures'
    base_name = f"test_{participant_id}_{timepoint}_{condition}"
    
    # Generate test figures
    plot_connectivity_matrix(
        analysis['connectivity_matrix'], 
        "Test Matrix", 
        os.path.join(figures_dir, f"{base_name}_matrix.png")
    )
    
    plot_network_graph(
        G, 
        "Test Network", 
        os.path.join(figures_dir, f"{base_name}_network.png")
    )
    
    plot_nodal_metrics(
        analysis['nodal'], 
        "Test Nodal Metrics", 
        os.path.join(figures_dir, f"{base_name}_nodal.png")
    )
    
    plot_pairwise_comparison(
        analysis['pairwise'], 
        "Test Pairwise Comparison", 
        os.path.join(figures_dir, f"{base_name}_pairwise.png")
    )
    
    plot_global_metrics(
        analysis['global'], 
        "Test Global Metrics", 
        os.path.join(figures_dir, f"{base_name}_global.png")
    )
    
    print("\nTest completed. Check the output/figures directory for generated visualizations.")

if __name__ == "__main__":
    test_analysis() 