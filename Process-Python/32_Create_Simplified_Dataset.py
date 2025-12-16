import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_dir = os.path.join(base_dir, "08-Data-Remerge")
input_file = os.path.join(input_dir, "02-Merged_Recheck_Deduplicated.csv")
output_file = os.path.join(input_dir, "03-Merged_Recheck_Simplified.csv")

def create_simplified_dataset():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    print(f"Original columns: {df.columns.tolist()}")

    # Select specific columns
    cols_to_keep = ['Refined_Formal_Name', 'Refined_Category', 'Status/Notes']
    
    # Check if columns exist
    missing_cols = [c for c in cols_to_keep if c not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns {missing_cols}")
        return

    df_simplified = df[cols_to_keep]

    print(f"Simplified dataset shape: {df_simplified.shape}")
    
    # Save
    df_simplified.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Saved simplified dataset to {output_file}")
    print("\nFirst 5 rows:")
    print(df_simplified.head())

if __name__ == "__main__":
    create_simplified_dataset()
