import pandas as pd
import numpy as np
import os
import networkx as nx
from pathlib import Path

class GrangerCausalityAnalyzer:
    def __init__(self):
        self.data_files = []
        self.processed_data = {}
        self.analyses = {}
        self.conditions = []
        self.participant_ids = []
        self.timepoints = []
        
    def load_data(self, file_path):
        """
        Load a single Excel file containing Granger Causality data
        
        Args:
            file_path (str): Path to the Excel file
        
        Returns:
            pandas.DataFrame: Processed GC matrix
        """
        # Extract metadata from filename
        file_name = os.path.basename(file_path)
        metadata = self._extract_metadata_from_filename(file_name)
        
        # Read and process the Excel file
        df = pd.read_excel(file_path)
        
        # Process the dataframe to ensure correct format
        if '\\' in df.columns:
            df = df.rename(columns={'\\': 'Source'})
            df = df.set_index('Source')
        
        # Store the processed data with metadata
        key = (metadata['participant_id'], metadata['timepoint'], metadata['condition'])
        self.processed_data[key] = df
        
        # Update our tracking lists
        if metadata['participant_id'] not in self.participant_ids:
            self.participant_ids.append(metadata['participant_id'])
        if metadata['timepoint'] not in self.timepoints:
            self.timepoints.append(metadata['timepoint'])
        if metadata['condition'] not in self.conditions:
            self.conditions.append(metadata['condition'])
        
        # Add file to our list
        self.data_files.append(file_path)
        
        return df
    
    def load_data_with_metadata(self, file_path, metadata):
        """
        Load a single Excel file with custom metadata
        
        Args:
            file_path (str): Path to the Excel file
            metadata (dict): Dictionary with keys for 'participant_id', 'timepoint', 'condition'
            
        Returns:
            pandas.DataFrame: Processed GC matrix
        """
        # Validate the metadata
        required_keys = ['participant_id', 'timepoint', 'condition']
        for key in required_keys:
            if key not in metadata:
                raise ValueError(f"Metadata is missing required key: {key}")
        
        # Read and process the Excel file
        df = pd.read_excel(file_path)
        
        # Process the dataframe to ensure correct format
        if '\\' in df.columns:
            df = df.rename(columns={'\\': 'Source'})
            df = df.set_index('Source')
        
        # Store the processed data with metadata
        key = (metadata['participant_id'], metadata['timepoint'], metadata['condition'])
        self.processed_data[key] = df
        
        # Update our tracking lists
        if metadata['participant_id'] not in self.participant_ids:
            self.participant_ids.append(metadata['participant_id'])
        if metadata['timepoint'] not in self.timepoints:
            self.timepoints.append(metadata['timepoint'])
        if metadata['condition'] not in self.conditions:
            self.conditions.append(metadata['condition'])
        
        # Add file to our list
        self.data_files.append(file_path)
        
        return df
    
    def load_multiple_files(self, directory_path=None, file_paths=None):
        """
        Load multiple Excel files containing Granger Causality data
        
        Args:
            directory_path (str, optional): Directory containing Excel files
            file_paths (list, optional): List of specific file paths
        """
        if directory_path:
            # Get all Excel files in the directory
            files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) 
                     if f.endswith('.xlsx') or f.endswith('.xls')]
        elif file_paths:
            files = file_paths
        else:
            raise ValueError("Either directory_path or file_paths must be provided")
        
        # Load each file
        for file_path in files:
            self.load_data(file_path)
    
    def load_multiple_files_with_metadata(self, file_paths_metadata):
        """
        Load multiple Excel files with custom metadata
        
        Args:
            file_paths_metadata (list): List of tuples containing (file_path, metadata_dict)
        """
        if not file_paths_metadata:
            raise ValueError("No files provided")
        
        # Load each file with its metadata
        for file_path, metadata in file_paths_metadata:
            self.load_data_with_metadata(file_path, metadata)
    
    def _extract_metadata_from_filename(self, file_name):
        """
        Extract metadata (participant ID, timepoint, condition) from the filename
        
        Args:
            file_name (str): The name of the file
            
        Returns:
            dict: Metadata extracted from the filename
        """
        # Remove extension
        base_name = os.path.splitext(file_name)[0]
        
        # Try to parse based on expected naming convention: UTF-[ID]_T[timepoint]_[condition]
        parts = base_name.split('_')
        
        # Initialize with default values
        metadata = {
            'participant_id': 'unknown',
            'timepoint': 'unknown',
            'condition': 'unknown'
        }
        
        # Extract participant ID
        if len(parts) > 0 and parts[0].startswith('UTF-'):
            metadata['participant_id'] = parts[0].replace('UTF-', '')
        
        # Extract timepoint
        if len(parts) > 1 and parts[1].startswith('T'):
            metadata['timepoint'] = parts[1]
        
        # Extract condition
        if len(parts) > 2:
            metadata['condition'] = parts[2]
        
        return metadata
    
    def analyze_all_data(self):
        """
        Run all analyses on the loaded data
        """
        for key, df in self.processed_data.items():
            participant_id, timepoint, condition = key
            
            # Create analysis key
            analysis_key = f"{participant_id}_{timepoint}_{condition}"
            
            # Perform the analyses
            results = {
                'connectivity_matrix': df.copy(),
                'pairwise': self.analyze_pairwise_connectivity(df),
                'nodal': self.analyze_nodal_metrics(df),
                'global': self.analyze_global_metrics(df),
                'metadata': {
                    'participant_id': participant_id,
                    'timepoint': timepoint,
                    'condition': condition
                }
            }
            
            # Store the results
            self.analyses[analysis_key] = results
    
    def analyze_pairwise_connectivity(self, df):
        """
        Analyze pairwise Granger Causality connections
        
        Args:
            df (pandas.DataFrame): GC matrix
            
        Returns:
            dict: Pairwise connectivity analyses
        """
        results = {
            'directional_pairs': {},
            'asymmetry_indices': {}
        }
        
        # Get electrode names
        electrodes = df.index.tolist()
        
        # Calculate directional pairs
        for source in electrodes:
            for target in electrodes:
                if source != target:
                    # Get the GC values in both directions
                    gc_source_to_target = df.loc[source, target]
                    gc_target_to_source = df.loc[target, source]
                    
                    # Store the pair
                    pair_name = f"{source}→{target}"
                    results['directional_pairs'][pair_name] = gc_source_to_target
                    
                    # Calculate asymmetry index for this pair
                    # (positive = source dominates, negative = target dominates)
                    if gc_source_to_target + gc_target_to_source > 0:
                        asymmetry = (gc_source_to_target - gc_target_to_source) / (gc_source_to_target + gc_target_to_source)
                    else:
                        asymmetry = 0
                    
                    results['asymmetry_indices'][f"{source}↔{target}"] = asymmetry
        
        return results
    
    def analyze_nodal_metrics(self, df):
        """
        Calculate nodal-level metrics (in-strength, out-strength, causal flow)
        
        Args:
            df (pandas.DataFrame): GC matrix
            
        Returns:
            dict: Nodal metrics for each electrode
        """
        results = {}
        
        # Get electrode names
        electrodes = df.index.tolist()
        
        for electrode in electrodes:
            # Out-strength: sum of outgoing connections (row sum excluding self)
            out_strength = df.loc[electrode].sum() - df.loc[electrode, electrode]
            
            # In-strength: sum of incoming connections (column sum excluding self)
            in_strength = df[electrode].sum() - df.loc[electrode, electrode]
            
            # Causal flow: out-strength minus in-strength
            causal_flow = out_strength - in_strength
            
            # Node category based on causal flow
            if causal_flow > 0:
                category = "sender"
            elif causal_flow < 0:
                category = "receiver"
            else:
                category = "neutral"
            
            # Store metrics for this electrode
            results[electrode] = {
                'in_strength': in_strength,
                'out_strength': out_strength,
                'causal_flow': causal_flow,
                'category': category
            }
        
        return results
    
    def analyze_global_metrics(self, df):
        """
        Calculate global metrics (overall connectivity, density, etc.)
        
        Args:
            df (pandas.DataFrame): GC matrix
            
        Returns:
            dict: Global metrics
        """
        # Get matrix excluding diagonal (self-connections)
        np.fill_diagonal(df.values, np.nan)
        gc_values = df.values.flatten()
        gc_values = gc_values[~np.isnan(gc_values)]
        
        # Restore diagonal values
        np.fill_diagonal(df.values, df.values.diagonal())
        
        # Calculate global metrics
        results = {
            'global_gc_strength': np.sum(gc_values),
            'mean_gc_strength': np.mean(gc_values),
            'median_gc_strength': np.median(gc_values),
            'max_gc_strength': np.max(gc_values),
            'min_gc_strength': np.min(gc_values),
            'std_gc_strength': np.std(gc_values)
        }
        
        # Calculate network density with different thresholds
        thresholds = [0.0001, 0.0005, 0.001]
        for threshold in thresholds:
            binary_matrix = (df.values > threshold).astype(int)
            np.fill_diagonal(binary_matrix, 0)  # Remove self-connections
            n_nodes = len(df)
            max_edges = n_nodes * (n_nodes - 1)  # Maximum possible directed edges
            density = np.sum(binary_matrix) / max_edges
            results[f'network_density_th{threshold}'] = density
        
        return results
    
    def get_group_statistics(self, filter_condition=None, filter_timepoint=None):
        """
        Calculate group-level statistics across participants
        
        Args:
            filter_condition (str, optional): Filter by specific condition
            filter_timepoint (str, optional): Filter by specific timepoint
            
        Returns:
            dict: Group-level statistics
        """
        # Filter analyses based on criteria
        filtered_analyses = {}
        
        for key, analysis in self.analyses.items():
            metadata = analysis['metadata']
            condition_match = filter_condition is None or metadata['condition'] == filter_condition
            timepoint_match = filter_timepoint is None or metadata['timepoint'] == filter_timepoint
            
            if condition_match and timepoint_match:
                filtered_analyses[key] = analysis
        
        if not filtered_analyses:
            return {"error": "No matching analyses found with the specified filters"}
        
        # Prepare group results
        group_results = {
            'nodal': self._group_nodal_metrics(filtered_analyses),
            'global': self._group_global_metrics(filtered_analyses),
            'pairwise': self._group_pairwise_metrics(filtered_analyses)
        }
        
        return group_results
    
    def _group_nodal_metrics(self, analyses):
        """Aggregate nodal metrics across analyses"""
        # Initialize storage for each electrode
        all_electrodes = set()
        for analysis in analyses.values():
            all_electrodes.update(analysis['nodal'].keys())
        
        grouped_nodal = {electrode: {
            'in_strength': [],
            'out_strength': [],
            'causal_flow': [],
            'categories': []
        } for electrode in all_electrodes}
        
        # Collect metrics across analyses
        for analysis in analyses.values():
            for electrode, metrics in analysis['nodal'].items():
                grouped_nodal[electrode]['in_strength'].append(metrics['in_strength'])
                grouped_nodal[electrode]['out_strength'].append(metrics['out_strength'])
                grouped_nodal[electrode]['causal_flow'].append(metrics['causal_flow'])
                grouped_nodal[electrode]['categories'].append(metrics['category'])
        
        # Calculate summary statistics
        result = {}
        for electrode, metrics in grouped_nodal.items():
            result[electrode] = {
                'in_strength_mean': np.mean(metrics['in_strength']),
                'in_strength_std': np.std(metrics['in_strength']),
                'out_strength_mean': np.mean(metrics['out_strength']),
                'out_strength_std': np.std(metrics['out_strength']),
                'causal_flow_mean': np.mean(metrics['causal_flow']),
                'causal_flow_std': np.std(metrics['causal_flow']),
                'dominant_category': max(set(metrics['categories']), key=metrics['categories'].count)
            }
        
        return result
    
    def _group_global_metrics(self, analyses):
        """Aggregate global metrics across analyses"""
        # Initialize storage for each metric
        metric_keys = next(iter(analyses.values()))['global'].keys()
        grouped_global = {metric: [] for metric in metric_keys}
        
        # Collect metrics across analyses
        for analysis in analyses.values():
            for metric, value in analysis['global'].items():
                grouped_global[metric].append(value)
        
        # Calculate summary statistics
        result = {}
        for metric, values in grouped_global.items():
            result[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values)
            }
        
        return result
    
    def _group_pairwise_metrics(self, analyses):
        """Aggregate pairwise metrics across analyses"""
        # Get all possible pairs
        all_pairs = set()
        for analysis in analyses.values():
            all_pairs.update(analysis['pairwise']['directional_pairs'].keys())
        
        # Initialize storage
        grouped_pairs = {pair: [] for pair in all_pairs}
        
        # Collect metrics across analyses
        for analysis in analyses.values():
            for pair, value in analysis['pairwise']['directional_pairs'].items():
                if pair in grouped_pairs:
                    grouped_pairs[pair].append(value)
        
        # Calculate summary statistics
        result = {}
        for pair, values in grouped_pairs.items():
            if values:  # Check if there are values for this pair
                result[pair] = {
                    'mean': np.mean(values),
                    'std': np.std(values)
                }
        
        return result
    
    def create_network_graph(self, analysis_key, threshold=0.0005):
        """
        Create a NetworkX graph from a GC matrix
        
        Args:
            analysis_key (str): Key for the analysis to use
            threshold (float): Threshold for including edges
            
        Returns:
            networkx.DiGraph: Directed graph representing the GC network
        """
        if analysis_key not in self.analyses:
            raise ValueError(f"Analysis key {analysis_key} not found")
        
        # Get the GC matrix
        gc_matrix = self.analyses[analysis_key]['connectivity_matrix']
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for electrode in gc_matrix.index:
            G.add_node(electrode)
        
        # Add edges with weights above threshold
        for source in gc_matrix.index:
            for target in gc_matrix.columns:
                if source != target and gc_matrix.loc[source, target] > threshold:
                    G.add_edge(source, target, weight=gc_matrix.loc[source, target])
        
        return G
    
    def get_group_statistics_by_participant(self, participant_id):
        """
        Get statistics for a specific participant across all conditions and timepoints
        
        Args:
            participant_id (str): Participant ID to filter by
            
        Returns:
            dict: Statistics for the participant
        """
        # Filter analyses for this participant
        filtered_analyses = {}
        
        for key, analysis in self.analyses.items():
            if analysis['metadata']['participant_id'] == participant_id:
                filtered_analyses[key] = analysis
        
        if not filtered_analyses:
            return {"error": f"No analyses found for participant {participant_id}"}
        
        # Prepare group results
        group_results = {
            'nodal': self._group_nodal_metrics(filtered_analyses),
            'global': self._group_global_metrics(filtered_analyses),
            'pairwise': self._group_pairwise_metrics(filtered_analyses),
            'metadata': {
                'participant_id': participant_id,
                'num_analyses': len(filtered_analyses)
            }
        }
        
        return group_results
    
    def get_condition_comparison(self, condition1, condition2, filter_timepoint=None):
        """
        Compare metrics between two conditions
        
        Args:
            condition1 (str): First condition to compare
            condition2 (str): Second condition to compare
            filter_timepoint (str, optional): Filter by specific timepoint
            
        Returns:
            dict: Comparison results
        """
        # Get statistics for each condition
        stats1 = self.get_group_statistics(filter_condition=condition1, filter_timepoint=filter_timepoint)
        stats2 = self.get_group_statistics(filter_condition=condition2, filter_timepoint=filter_timepoint)
        
        if "error" in stats1 or "error" in stats2:
            return {"error": "Could not get statistics for one or both conditions"}
        
        # Compare global metrics
        global_comparison = {}
        for metric in stats1['global'].keys():
            diff = stats2['global'][metric]['mean'] - stats1['global'][metric]['mean']
            percent_change = (diff / stats1['global'][metric]['mean']) * 100 if stats1['global'][metric]['mean'] != 0 else float('inf')
            
            global_comparison[metric] = {
                'condition1_mean': stats1['global'][metric]['mean'],
                'condition2_mean': stats2['global'][metric]['mean'],
                'absolute_diff': diff,
                'percent_change': percent_change
            }
        
        # Compare nodal metrics
        nodal_comparison = {}
        shared_electrodes = set(stats1['nodal'].keys()).intersection(set(stats2['nodal'].keys()))
        
        for electrode in shared_electrodes:
            nodal_comparison[electrode] = {}
            
            for metric in ['in_strength_mean', 'out_strength_mean', 'causal_flow_mean']:
                diff = stats2['nodal'][electrode][metric] - stats1['nodal'][electrode][metric]
                percent_change = (diff / stats1['nodal'][electrode][metric]) * 100 if stats1['nodal'][electrode][metric] != 0 else float('inf')
                
                nodal_comparison[electrode][metric] = {
                    'condition1': stats1['nodal'][electrode][metric],
                    'condition2': stats2['nodal'][electrode][metric],
                    'absolute_diff': diff,
                    'percent_change': percent_change
                }
            
            # Compare categories
            nodal_comparison[electrode]['category_change'] = {
                'condition1': stats1['nodal'][electrode]['dominant_category'],
                'condition2': stats2['nodal'][electrode]['dominant_category'],
                'changed': stats1['nodal'][electrode]['dominant_category'] != stats2['nodal'][electrode]['dominant_category']
            }
        
        # Compare pairwise metrics
        pairwise_comparison = {}
        shared_pairs = set(stats1['pairwise'].keys()).intersection(set(stats2['pairwise'].keys()))
        
        for pair in shared_pairs:
            diff = stats2['pairwise'][pair]['mean'] - stats1['pairwise'][pair]['mean']
            percent_change = (diff / stats1['pairwise'][pair]['mean']) * 100 if stats1['pairwise'][pair]['mean'] != 0 else float('inf')
            
            pairwise_comparison[pair] = {
                'condition1_mean': stats1['pairwise'][pair]['mean'],
                'condition2_mean': stats2['pairwise'][pair]['mean'],
                'absolute_diff': diff,
                'percent_change': percent_change
            }
        
        return {
            'global': global_comparison,
            'nodal': nodal_comparison,
            'pairwise': pairwise_comparison,
            'metadata': {
                'condition1': condition1,
                'condition2': condition2,
                'timepoint': filter_timepoint
            }
        }
    
    def get_timepoint_comparison(self, timepoint1, timepoint2, filter_condition=None):
        """
        Compare metrics between two timepoints
        
        Args:
            timepoint1 (str): First timepoint to compare
            timepoint2 (str): Second timepoint to compare
            filter_condition (str, optional): Filter by specific condition
            
        Returns:
            dict: Comparison results
        """
        # Get statistics for each timepoint
        stats1 = self.get_group_statistics(filter_timepoint=timepoint1, filter_condition=filter_condition)
        stats2 = self.get_group_statistics(filter_timepoint=timepoint2, filter_condition=filter_condition)
        
        if "error" in stats1 or "error" in stats2:
            return {"error": "Could not get statistics for one or both timepoints"}
        
        # Compare global metrics
        global_comparison = {}
        for metric in stats1['global'].keys():
            diff = stats2['global'][metric]['mean'] - stats1['global'][metric]['mean']
            percent_change = (diff / stats1['global'][metric]['mean']) * 100 if stats1['global'][metric]['mean'] != 0 else float('inf')
            
            global_comparison[metric] = {
                'timepoint1_mean': stats1['global'][metric]['mean'],
                'timepoint2_mean': stats2['global'][metric]['mean'],
                'absolute_diff': diff,
                'percent_change': percent_change
            }
        
        # Compare nodal metrics
        nodal_comparison = {}
        shared_electrodes = set(stats1['nodal'].keys()).intersection(set(stats2['nodal'].keys()))
        
        for electrode in shared_electrodes:
            nodal_comparison[electrode] = {}
            
            for metric in ['in_strength_mean', 'out_strength_mean', 'causal_flow_mean']:
                diff = stats2['nodal'][electrode][metric] - stats1['nodal'][electrode][metric]
                percent_change = (diff / stats1['nodal'][electrode][metric]) * 100 if stats1['nodal'][electrode][metric] != 0 else float('inf')
                
                nodal_comparison[electrode][metric] = {
                    'timepoint1': stats1['nodal'][electrode][metric],
                    'timepoint2': stats2['nodal'][electrode][metric],
                    'absolute_diff': diff,
                    'percent_change': percent_change
                }
            
            # Compare categories
            nodal_comparison[electrode]['category_change'] = {
                'timepoint1': stats1['nodal'][electrode]['dominant_category'],
                'timepoint2': stats2['nodal'][electrode]['dominant_category'],
                'changed': stats1['nodal'][electrode]['dominant_category'] != stats2['nodal'][electrode]['dominant_category']
            }
        
        # Compare pairwise metrics
        pairwise_comparison = {}
        shared_pairs = set(stats1['pairwise'].keys()).intersection(set(stats2['pairwise'].keys()))
        
        for pair in shared_pairs:
            diff = stats2['pairwise'][pair]['mean'] - stats1['pairwise'][pair]['mean']
            percent_change = (diff / stats1['pairwise'][pair]['mean']) * 100 if stats1['pairwise'][pair]['mean'] != 0 else float('inf')
            
            pairwise_comparison[pair] = {
                'timepoint1_mean': stats1['pairwise'][pair]['mean'],
                'timepoint2_mean': stats2['pairwise'][pair]['mean'],
                'absolute_diff': diff,
                'percent_change': percent_change
            }
        
        return {
            'global': global_comparison,
            'nodal': nodal_comparison,
            'pairwise': pairwise_comparison,
            'metadata': {
                'timepoint1': timepoint1,
                'timepoint2': timepoint2,
                'condition': filter_condition
            }
        }
    
    def create_combined_table(self, variables=None, filter_conditions=None, filter_timepoints=None, filter_participants=None):
        """
        Create a combined table with all values for specified variables
        
        Args:
            variables (list, optional): List of variable types to include ('global', 'nodal', 'pairwise')
            filter_conditions (list, optional): List of conditions to include
            filter_timepoints (list, optional): List of timepoints to include
            filter_participants (list, optional): List of participant IDs to include
            
        Returns:
            pandas.DataFrame: Combined table
        """
        if not self.analyses:
            print("No analyses available")
            return None
        
        # Default to all variable types if none specified
        if variables is None:
            variables = ['global', 'nodal', 'pairwise']
        
        all_rows = []
        
        for key, analysis in self.analyses.items():
            metadata = analysis['metadata']
            
            # Apply filters
            if filter_conditions and metadata['condition'] not in filter_conditions:
                continue
            if filter_timepoints and metadata['timepoint'] not in filter_timepoints:
                continue
            if filter_participants and metadata['participant_id'] not in filter_participants:
                continue
            
            # Create base row with metadata
            base_row = {
                'Participant': metadata['participant_id'],
                'Condition': metadata['condition'],
                'Timepoint': metadata['timepoint']
            }
            
            # Add global metrics
            if 'global' in variables:
                for metric, value in analysis['global'].items():
                    new_row = base_row.copy()
                    new_row['Metric_Type'] = 'Global'
                    new_row['Variable'] = metric
                    new_row['Value'] = value
                    all_rows.append(new_row)
            
            # Add nodal metrics
            if 'nodal' in variables:
                for electrode, metrics in analysis['nodal'].items():
                    for metric, value in metrics.items():
                        if metric != 'category':  # Skip categorical data for now
                            new_row = base_row.copy()
                            new_row['Metric_Type'] = 'Nodal'
                            new_row['Electrode'] = electrode
                            new_row['Variable'] = metric
                            new_row['Value'] = value
                            all_rows.append(new_row)
            
            # Add pairwise metrics
            if 'pairwise' in variables:
                for pair, value in analysis['pairwise']['directional_pairs'].items():
                    source, target = pair.split('→')
                    new_row = base_row.copy()
                    new_row['Metric_Type'] = 'Pairwise'
                    new_row['Source'] = source
                    new_row['Target'] = target
                    new_row['Variable'] = 'GC Value'
                    new_row['Value'] = value
                    all_rows.append(new_row)
        
        if not all_rows:
            print("No data matches the filters")
            return None
        
        return pd.DataFrame(all_rows)
    
    def create_group_tables(self, groupby=None, variables=None, filter_conditions=None, filter_timepoints=None, filter_participants=None):
        """
        Create tables with group statistics for different groupings
        
        Args:
            groupby (str): How to group the data ('condition', 'timepoint', 'participant', 'condition_timepoint')
            variables (list, optional): List of variable types to include ('global', 'nodal', 'pairwise')
            filter_conditions (list, optional): List of conditions to include
            filter_timepoints (list, optional): List of timepoints to include
            filter_participants (list, optional): List of participant IDs to include
            
        Returns:
            dict: Dictionary of DataFrames
        """
        # Get combined table
        combined_df = self.create_combined_table(variables, filter_conditions, filter_timepoints, filter_participants)
        
        if combined_df is None:
            return None
        
        tables = {'combined': combined_df}
        
        # Define valid groupby options
        valid_groupby = ['condition', 'timepoint', 'participant', 'condition_timepoint']
        if groupby and groupby not in valid_groupby:
            print(f"Invalid groupby value. Must be one of: {', '.join(valid_groupby)}")
            return tables
        
        # Group data based on groupby parameter
        if groupby == 'condition':
            groups = combined_df['Condition'].unique()
            for group in groups:
                filtered_df = combined_df[combined_df['Condition'] == group]
                tables[f"condition_{group}"] = filtered_df
                
                # Create summary table
                summary = self._create_summary_table(filtered_df)
                tables[f"condition_{group}_summary"] = summary
                
        elif groupby == 'timepoint':
            groups = combined_df['Timepoint'].unique()
            for group in groups:
                filtered_df = combined_df[combined_df['Timepoint'] == group]
                tables[f"timepoint_{group}"] = filtered_df
                
                # Create summary table
                summary = self._create_summary_table(filtered_df)
                tables[f"timepoint_{group}_summary"] = summary
                
        elif groupby == 'participant':
            groups = combined_df['Participant'].unique()
            for group in groups:
                filtered_df = combined_df[combined_df['Participant'] == group]
                tables[f"participant_{group}"] = filtered_df
                
                # Create summary table
                summary = self._create_summary_table(filtered_df)
                tables[f"participant_{group}_summary"] = summary
                
        elif groupby == 'condition_timepoint':
            # Group by both condition and timepoint
            conditions = combined_df['Condition'].unique()
            timepoints = combined_df['Timepoint'].unique()
            
            for condition in conditions:
                for timepoint in timepoints:
                    filtered_df = combined_df[(combined_df['Condition'] == condition) & 
                                             (combined_df['Timepoint'] == timepoint)]
                    
                    if not filtered_df.empty:
                        tables[f"condition_{condition}_timepoint_{timepoint}"] = filtered_df
                        
                        # Create summary table
                        summary = self._create_summary_table(filtered_df)
                        tables[f"condition_{condition}_timepoint_{timepoint}_summary"] = summary
        
        # Create a combined summary table
        tables['combined_summary'] = self._create_summary_table(combined_df)
        
        return tables
    
    def _create_summary_table(self, df):
        """
        Create a summary table with statistics from a dataframe
        
        Args:
            df (pandas.DataFrame): DataFrame to summarize
            
        Returns:
            pandas.DataFrame: Summary statistics
        """
        if df.empty:
            return pd.DataFrame()
        
        # Define groupby columns based on what's in the dataframe
        groupby_cols = ['Metric_Type', 'Variable']
        
        if 'Electrode' in df.columns:
            groupby_cols.append('Electrode')
        
        if 'Source' in df.columns and 'Target' in df.columns:
            groupby_cols.extend(['Source', 'Target'])
        
        # Group and calculate statistics
        summary = df.groupby(groupby_cols)['Value'].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()
        
        return summary
    
    def export_tables_to_csv(self, tables, output_dir='output/tables'):
        """
        Export tables to CSV files
        
        Args:
            tables (dict): Dictionary of DataFrames to export
            output_dir (str): Directory to save CSV files
            
        Returns:
            list: Paths to saved CSV files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for name, df in tables.items():
            if df is not None and not df.empty:
                file_path = os.path.join(output_dir, f"{name}.csv")
                df.to_csv(file_path, index=False)
                saved_files.append(file_path)
                print(f"Saved table to {file_path}")
        
        return saved_files 