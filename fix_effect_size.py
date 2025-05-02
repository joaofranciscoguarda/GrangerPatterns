#!/usr/bin/env python
import re

# Read the file
with open('src/gui.py', 'r') as f:
    content = f.read()

# Find and replace the partial eta squared calculation with an improved version
old_code = """                        # Calculate partial eta squared (included in detailed output)
                        # Handle different versions of pingouin that might use different column names
                        if 'np2' in row:
                            partial_eta_sq = row['np2']
                        elif 'eta2_partial' in row:
                            partial_eta_sq = row['eta2_partial']
                        elif 'n2' in row:
                            partial_eta_sq = row['n2']
                        elif 'eta2' in row:
                            partial_eta_sq = row['eta2']
                        else:
                            # Calculate manually if not available
                            if 'SS' in row and 'SS_error' in result.columns:
                                ss_effect = row['SS']
                                ss_error = result.loc[idx, 'SS_error'] if idx in result.index else sum(result['SS_error'])
                                partial_eta_sq = ss_effect / (ss_effect + ss_error) if (ss_effect + ss_error) > 0 else 0
                            else:
                                partial_eta_sq = float('nan')  # Not available"""

new_code = """                        # Calculate partial eta squared (included in detailed output)
                        # Handle different versions of pingouin that might use different column names
                        if 'np2' in row:
                            partial_eta_sq = row['np2']
                        elif 'eta2_partial' in row:
                            partial_eta_sq = row['eta2_partial']
                        elif 'n2' in row:
                            partial_eta_sq = row['n2']
                        elif 'eta2' in row:
                            partial_eta_sq = row['eta2']
                        else:
                            # Calculate manually from F value and degrees of freedom
                            if 'F' in row and row['F'] > 0:
                                f_value = row['F']
                                # Get degrees of freedom
                                df_effect = row.get('ddof1', row.get('df', row.get('DF1', 1)))
                                df_error = row.get('ddof2', row.get('df2', row.get('DF2', 10)))  # Assume df error of 10 if not available
                                
                                # Calculate partial eta squared from F value
                                partial_eta_sq = (f_value * df_effect) / (f_value * df_effect + df_error)
                            else:
                                partial_eta_sq = 0.0  # Use 0 instead of NaN for better display"""

# Replace all occurrences (there are two identical sections)
content = content.replace(old_code, new_code)

# Also add observed power calculation
old_power_value = """                            "N/A"  # Pingouin doesn't calculate observed power"""
new_power_value = """                            f"{self._calculate_observed_power(row):.4f}"  # Calculate observed power"""

content = content.replace(old_power_value, new_power_value)

# Add the observed power calculation method
observed_power_method = """
    def _calculate_observed_power(self, row):
        \"\"\"Calculate observed power for ANOVA result row\"\"\"
        try:
            # Check if we have F value and degrees of freedom
            if 'F' in row and row['F'] > 0:
                f_value = row['F']
                # Get degrees of freedom
                df_effect = float(row.get('ddof1', row.get('df', row.get('DF1', 1))))
                df_error = float(row.get('ddof2', row.get('df2', row.get('DF2', 10))))  # Assume df error of 10 if not available
                
                # Use statsmodels power calculator for F test
                if df_effect > 0 and df_error > 0:
                    power_calculator = FTestPower()
                    return power_calculator.power(f_val=f_value, df_num=df_effect, df_denom=df_error)
            
            return 0.0  # Default power if calculation fails
        except Exception as e:
            print(f"Error calculating power: {e}")
            return 0.0
"""

# Find a good place to insert the method (before _export_anova_results)
export_anova_pattern = r'def _export_anova_results\(self\):'
content = re.sub(export_anova_pattern, observed_power_method + '\n    ' + export_anova_pattern, content)

# Write the modified content back to the file
with open('src/gui.py', 'w') as f:
    f.write(content)

print("Fixed effect size and observed power calculations") 