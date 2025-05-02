#!/usr/bin/env python
import re

# Read the file
with open('src/gui.py', 'r') as f:
    content = f.readlines()

# Find the start and end of the function to remove
start_line = None
end_line = None
in_function = False
opening_count = 0
closing_count = 0

for i, line in enumerate(content):
    if 'def _add_posthoc_results_to_tree' in line:
        start_line = i
        in_function = True
    
    if in_function:
        # Count opening and closing braces to determine the function scope
        opening_count += line.count('{')
        closing_count += line.count('}')
        
        # Look for the start of the next function or the end of the class
        if line.strip().startswith('def ') and i > start_line:
            end_line = i
            break

# If we didn't find the end by the time we reach another function,
# but we're still tracking the function, it means the function extends to the end of the file
if in_function and not end_line:
    end_line = len(content)

# Remove the function
if start_line is not None and end_line is not None:
    print(f"Removing unused function from lines {start_line+1} to {end_line}")
    new_content = content[:start_line] + content[end_line:]
    
    # Write the file back
    with open('src/gui.py', 'w') as f:
        f.writelines(new_content)
    
    print(f"Removed unused function _add_posthoc_results_to_tree")
else:
    print("Function not found or could not determine function boundaries.") 