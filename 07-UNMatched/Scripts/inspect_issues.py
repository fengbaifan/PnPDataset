import pandas as pd
import os

files = [f"{i}.csv" for i in range(1, 10)]
dfs = []

for file in files:
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            df['Source_File'] = file
            dfs.append(df)
        except Exception:
            pass

all_data = pd.concat(dfs, ignore_index=True)

print("--- Detailed Duplicate Analysis ---")
duplicates = all_data[all_data.duplicated(subset=['Original_Entry'], keep=False)]
if not duplicates.empty:
    print(duplicates[['Original_Entry', 'Refined_Formal_Name', 'Refined_Category', 'Source_File']].sort_values('Original_Entry').to_string())

print("\n--- Split Required Items ---")
split_items = all_data[all_data['Status/Notes'].str.contains('Split Required', na=False)]
if not split_items.empty:
    print(split_items[['Original_Entry', 'Refined_Formal_Name', 'Status/Notes', 'Source_File']].to_string())
