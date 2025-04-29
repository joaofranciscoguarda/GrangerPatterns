import pandas as pd
import os

# File path
file_path = os.path.join('data', 'UTF-8002_T2_Phase1.xlsx')

# Read Excel file
df = pd.read_excel(file_path)

# Print basic information
print("Excel file information:")
print(f"Shape: {df.shape}")
print("\nRaw Data:")
print(df)

# It seems the first row contains electrode names and first column might also contain electrode names
# Let's try to fix this by setting the first column as index and understanding the data better
print("\n\nREFORMATTING DATA:")
# Check if the first column contains a header marker like '\\'
first_col_name = df.columns[0]
if first_col_name == '\\':
    # This suggests the first column should contain row labels
    # Rename the index column to something more meaningful
    df = df.rename(columns={first_col_name: 'Source'})
    # Set the first column as index
    electrode_names = df['Source'].tolist()
    # Get actual electrode names from the data
    if 0 in df.index and isinstance(df.loc[0, 'Source'], str):
        # If first row has electrode name in 'Source' column, use those as electrode names
        electrode_names = df['Source'].tolist()
        df = df.set_index('Source')
    else:
        # Try to infer electrode names from column names (excluding the first column)
        electrode_names = [col for col in df.columns if col != 'Source']
        # Check if row indices (0, 1, 2...) match the number of electrodes
        if len(df) == len(electrode_names):
            # Create a new DataFrame with correct structure
            new_df = pd.DataFrame(
                df.values[:, 1:],  # Skip first column which contains '\\'
                index=electrode_names,  # Use electrode names as index
                columns=df.columns[1:]  # Use electrode names as columns (skip first column)
            )
            df = new_df
        else:
            # Just set index to Source column
            df = df.set_index('Source')

print("\nReformatted Data:")
print(df)

# Check if we now have electrode names as both rows and columns
print("\nElectrode Analysis:")
row_names = df.index.tolist()
col_names = df.columns.tolist()
print(f"Row names (Source): {row_names}")
print(f"Column names (Target): {col_names}")

# Print the values in a clear matrix
print("\nGranger Causality Matrix (Source → Target):")
print(df) 