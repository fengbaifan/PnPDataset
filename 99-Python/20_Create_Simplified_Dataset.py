import pandas as pd
import os

def create_simplified_dataset():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'08-EntityMerge\02-Deduplicated_Entities.csv')
    output_csv = os.path.join(base_dir, r'08-EntityMerge\03-Simplified_Entities.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Select columns: Entity_Name, Type, Original_Files
    # Rename Entity_Name -> Original Entity Name
    
    # Ensure columns exist
    required_cols = ['Entity_Name', 'Type', 'Original_Files']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Column '{col}' not found in input file.")
            return

    new_df = df[required_cols].copy()
    new_df = new_df.rename(columns={'Entity_Name': 'Original Entity Name'})
    
    print(f"Created simplified dataset with {len(new_df)} rows.")
    print(f"Columns: {list(new_df.columns)}")
    
    new_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved to {output_csv}")

if __name__ == "__main__":
    create_simplified_dataset()
