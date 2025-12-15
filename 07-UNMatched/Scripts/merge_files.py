import pandas as pd
import os

# List of files to merge
files = [f"{i}.csv" for i in range(1, 10)]
dfs = []

print("--- Merging Files ---")
for file in files:
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # We won't add Source_File unless requested, to keep the schema clean
            # df['Source_File'] = file 
            dfs.append(df)
            print(f"Loaded {file}: {len(df)} rows")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    else:
        print(f"File not found: {file}")

if dfs:
    merged_df = pd.concat(dfs, ignore_index=True)
    output_file = "merged_1_9.csv"
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig') # utf-8-sig for Excel compatibility
    print(f"\nSuccessfully merged {len(dfs)} files into '{output_file}'.")
    print(f"Total rows: {len(merged_df)}")
else:
    print("No data to merge.")
