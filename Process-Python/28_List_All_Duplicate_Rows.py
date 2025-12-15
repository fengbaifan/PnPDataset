import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")

def list_all_duplicate_rows():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    # Filter for duplicates based on Refined_Formal_Name
    dup_mask = df.duplicated(subset=['Refined_Formal_Name'], keep=False)
    dupes = df[dup_mask].sort_values(by=['Refined_Formal_Name', 'Original_Entry'])
    
    if dupes.empty:
        print("No duplicates found.")
        return

    print(f"\n=== Full List of Duplicate Rows ({len(dupes)} rows) ===")
    print(f"{'Refined_Formal_Name':<40} | {'Original_Entry':<40} | {'Note'}")
    print("-" * 100)
    
    current_name = ""
    for index, row in dupes.iterrows():
        name = str(row['Refined_Formal_Name'])
        original = str(row['Original_Entry'])
        note = str(row['Status/Notes'])
        
        # Truncate for display
        if len(name) > 37: name = name[:37] + "..."
        if len(original) > 37: original = original[:37] + "..."
        if len(note) > 20: note = note[:20] + "..."
        
        if row['Refined_Formal_Name'] != current_name:
            print("-" * 100) # Separator between groups
            current_name = row['Refined_Formal_Name']
            
        print(f"{name:<40} | {original:<40} | {note}")

if __name__ == "__main__":
    list_all_duplicate_rows()
