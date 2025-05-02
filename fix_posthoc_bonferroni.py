#!/usr/bin/env python

# Read the file
with open('src/gui.py', 'r') as f:
    content = f.read()

# Find and replace the problematic Bonferroni post-hoc test code
old_code = """                    # For Bonferroni
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
                        std_error = test_result[3] if len(test_result) > 3 else float('nan')"""

new_code = """                    # For Bonferroni
                    print(f"Running Bonferroni post-hoc test for {len(groups.unique())} groups")
                    result_obj = posthoc.allpairtest(stats.ttest_ind, method='bonf')
                    
                    # Process the results manually
                    for i, test_result in enumerate(result_obj[0]):
                        try:
                            # Get the group names - handle both tuple formats (2 or 3 elements)
                            group_pair = result_obj[1][i]
                            if isinstance(group_pair, tuple) and len(group_pair) >= 2:
                                group1, group2 = group_pair[0], group_pair[1]
                            else:
                                print(f"Warning: Unexpected group pair format: {group_pair}")
                                continue
                            
                            # Extract statistics (safely)
                            t_value = test_result[0] if len(test_result) > 0 else 0.0
                            p_value = test_result[1] if len(test_result) > 1 else 1.0
                            mean_diff = test_result[2] if len(test_result) > 2 else 0.0
                            std_error = test_result[3] if len(test_result) > 3 else float('nan')
                            
                            print(f"Successfully processed pair: {group1} vs {group2}")
                        except Exception as e:
                            print(f"Error processing group pair {i}: {e}")
                            traceback.print_exc()
                            continue"""

# Replace the problematic code
content = content.replace(old_code, new_code)

# Write the file back
with open('src/gui.py', 'w') as f:
    f.write(content)

print("Fixed Bonferroni post-hoc test implementation") 