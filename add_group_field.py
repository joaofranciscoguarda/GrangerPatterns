#!/usr/bin/env python

# The line after which we want to add code
target_line = 146

# The lines we want to add
new_lines = '''        # Group
        ttk.Label(form_frame, text="Group:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.group_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.group_var).grid(row=3, column=1, sticky="ew", padx=5, pady=5)
'''

# Read the file
with open('src/gui.py', 'r') as f:
    lines = f.readlines()

# Insert the new lines
lines.insert(target_line, new_lines)

# Write the file back
with open('src/gui.py', 'w') as f:
    f.writelines(lines)

print("Group field added to metadata form!")

# Now update the save_metadata method to include the group field
start_line = 0
for i, line in enumerate(lines):
    if "def save_metadata(self):" in line:
        start_line = i
        break

if start_line > 0:
    # Find where the metadata gets updated in the save_metadata method
    for i in range(start_line, len(lines)):
        if "info['timepoint'] = self.timepoint_var.get()" in lines[i]:
            # Add the group field after this line
            lines.insert(i + 1, "                info['group'] = self.group_var.get()\n")
            break
            
    # Find the update treeview section
    for i in range(start_line, len(lines)):
        if "self.file_tree.item(self.selected_item_id, values=(" in lines[i]:
            # The lines following this contain the values to update
            # We need to insert the group field in the values tuple
            j = i + 4  # This is the line after timepoint, before status
            lines.insert(j, "                    info['group'],\n")
            break

# Write the updated file
with open('src/gui.py', 'w') as f:
    f.writelines(lines)

print("save_metadata method updated to include group field!") 