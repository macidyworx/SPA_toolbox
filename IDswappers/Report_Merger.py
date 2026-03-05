import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog

# Hide the main window
root = tk.Tk()
root.withdraw()

# Open file dialog to select multiple Excel files
files = filedialog.askopenfilenames(
    title="Select Report Excel Files",
    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
)

if not files:
    print("No files selected. Exiting.")
    exit()

# Directory to save the merged report (same as the first file's directory)
output_dir = os.path.dirname(files[0])
output_path = os.path.join(output_dir, "FULL_Report.xlsx")

# Lists to collect data
summary_dfs = []
full_list_dfs = []

for file in files:
    try:
        # Read Summary sheet
        summary_df = pd.read_excel(file, sheet_name='Summary')
        summary_dfs.append(summary_df)
        
        # Read Full List sheet
        full_list_df = pd.read_excel(file, sheet_name='Full List')
        full_list_dfs.append(full_list_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")
        continue

if not summary_dfs:
    print("No valid Summary sheets found. Exiting.")
    exit()

# Merge Summary: place side by side
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # For Summary tab
    start_col = 0
    for i, df in enumerate(summary_dfs):
        df.to_excel(writer, sheet_name='Summary', startcol=start_col, index=False)
        start_col += df.shape[1] + 1  # Add a gap column
    
    # For Full List tab: concatenate all
    if full_list_dfs:
        full_list_combined = pd.concat(full_list_dfs, ignore_index=True)
        full_list_combined.to_excel(writer, sheet_name='Full List', index=False)

print(f"Merged report saved to {output_path}")