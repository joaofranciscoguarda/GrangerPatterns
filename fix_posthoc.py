#!/usr/bin/env python

# Read the file
with open('src/gui.py', 'r') as f:
    content = f.read()

# Fix the post-hoc test by completely rewriting the method
old_code = '''    def _run_posthoc_test(self):
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
            messagebox.showerror("Post-hoc Test Error", f"Error running post-hoc test: {str(e)}")'''

new_code = '''    def _run_posthoc_test(self):
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
            
        # Helper function to safely run post-hoc tests
        def run_post_hoc_safely(values, groups):
            try:
                # Run the post-hoc test
                posthoc = MultiComparison(values, groups)
                
                if test_type == 'bonferroni':
                    # For Bonferroni
                    print(f"Running Bonferroni post-hoc test for {len(groups.unique())} groups")
                    result_obj = posthoc.allpairtest(stats.ttest_ind, method='bonf')
                    
                    # Process the results manually
                    for i, test_result in enumerate(result_obj[0]):
                        # Get the group names
                        group1, group2 = result_obj[1][i]
                        
                        # Extract statistics
                        t_value = test_result[0]
                        p_value = test_result[1]
                        mean_diff = test_result[2]
                        std_error = test_result[3] if len(test_result) > 3 else float('nan')
                        
                        is_significant = p_value < 0.05
                        
                        # Add to tree
                        values = [
                            group1, 
                            group2, 
                            f"{mean_diff:.4f}", 
                            f"{std_error:.4f}",
                            f"{t_value:.4f}", 
                            f"{p_value:.4f}", 
                            "Yes" if is_significant else "No"
                        ]
                        
                        item_id = self.posthoc_tree.insert('', 'end', values=values)
                        
                        if is_significant:
                            self.posthoc_tree.item(item_id, tags=('significant',))
                    
                else:  # Tukey HSD
                    print(f"Running Tukey HSD post-hoc test for {len(groups.unique())} groups")
                    result_obj = posthoc.tukeyhsd()
                    
                    # Process the Tukey results
                    result_data = result_obj._results_table.data[1:]  # Skip header row
                    for row_data in result_data:
                        # Handle different formats
                        if len(row_data) >= 6:
                            group1, group2, mean_diff, p_value, conf_lower, conf_upper = row_data[:6]
                        elif len(row_data) >= 4:
                            group1, group2, mean_diff, p_value = row_data[:4]
                            conf_lower = conf_upper = float('nan')
                        else:
                            print(f"Warning: Unexpected row format in Tukey results: {row_data}")
                            continue
                        
                        # Get standard error
                        std_error = getattr(result_obj, 'std_pairs', 1.0)
                        
                        # Calculate t-value if possible
                        t_value = mean_diff / std_error if std_error > 0 else float('nan')
                        
                        is_significant = p_value < 0.05
                        
                        # Add to tree
                        values = [
                            group1, 
                            group2, 
                            f"{mean_diff:.4f}", 
                            f"{std_error:.4f}",
                            f"{t_value:.4f}" if not isinstance(t_value, str) else t_value, 
                            f"{p_value:.4f}", 
                            "Yes" if is_significant else "No"
                        ]
                        
                        item_id = self.posthoc_tree.insert('', 'end', values=values)
                        
                        if is_significant:
                            self.posthoc_tree.item(item_id, tags=('significant',))
                
                return True
            except Exception as e:
                print(f"Error in post-hoc test: {str(e)}")
                traceback.print_exc()
                messagebox.showerror("Post-hoc Test Error", f"Error running post-hoc test: {str(e)}")
                return False
        
        try:
            # Run appropriate test based on factor
            if factor == 'condition' and 'Condition' in df.columns:
                # Run post-hoc test for condition
                if len(df['Condition'].unique()) < 2:
                    messagebox.showwarning("Insufficient Data", "Need at least two different conditions for post-hoc comparison")
                    return
                
                success = run_post_hoc_safely(df['Value'], df['Condition'])
                if success:
                    messagebox.showinfo("Post-hoc Test", f"Post-hoc test for Condition completed ({test_type})")
                
            elif factor == 'timepoint' and 'Timepoint' in df.columns:
                # Run post-hoc test for timepoint
                if len(df['Timepoint'].unique()) < 2:
                    messagebox.showwarning("Insufficient Data", "Need at least two different timepoints for post-hoc comparison")
                    return
                    
                success = run_post_hoc_safely(df['Value'], df['Timepoint'])
                if success:
                    messagebox.showinfo("Post-hoc Test", f"Post-hoc test for Timepoint completed ({test_type})")
                
            elif factor == 'interaction' and 'Condition' in df.columns and 'Timepoint' in df.columns:
                # Create interaction groups
                df['Interaction'] = df['Condition'] + '_' + df['Timepoint']
                
                if len(df['Interaction'].unique()) < 2:
                    messagebox.showwarning("Insufficient Data", "Need at least two different condition×timepoint combinations for post-hoc comparison")
                    return
                    
                success = run_post_hoc_safely(df['Value'], df['Interaction'])
                if success:
                    messagebox.showinfo("Post-hoc Test", f"Post-hoc test for Condition×Timepoint interaction completed ({test_type})")
                
            else:
                messagebox.showwarning("Invalid Selection", f"Cannot perform post-hoc test for factor: {factor}")
                return
                
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Post-hoc Test Error", f"Error running post-hoc test: {str(e)}")'''

# Replace the method
content = content.replace(old_code, new_code)

# Write the file back
with open('src/gui.py', 'w') as f:
    f.write(content)

print("Fixed post-hoc test implementation") 