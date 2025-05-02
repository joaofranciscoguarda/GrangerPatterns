#!/usr/bin/env python
import fileinput
import sys

start_line = 2644  # The line number where we want to start the replacement
end_line = 2650    # The line number where we want to end the replacement

# The replacement code
replacement = '''                # For mixed ANOVA, we need a between-subjects factor
                if anova_type == 'mixed':
                    if not self.factor_group.get() or 'Group' not in df.columns or len(df['Group'].unique()) < 2:
                        # Fall back to using Condition as between-subjects factor if Group is not available
                        if not include_condition or 'Condition' not in df.columns or len(df['Condition'].unique()) < 2:
                            messagebox.showwarning("Invalid Selection", 
                                                "Mixed ANOVA requires either 'Group' or 'Condition' factor with at least 2 levels")
                            return
'''

# Read the file
with open('src/gui.py', 'r') as f:
    lines = f.readlines()

# Replace the lines
new_lines = lines[:start_line]
new_lines.append(replacement)
new_lines.extend(lines[end_line:])

# Write the file back
with open('src/gui.py', 'w') as f:
    f.writelines(new_lines)

print("Mixed ANOVA code successfully updated!") 