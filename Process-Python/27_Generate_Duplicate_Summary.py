import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_file = os.path.join(base_dir, "Process-Python", "02-Analysis", "Recheck_Duplicate_Summary.csv")

def generate_duplicate_summary():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    # Filter for duplicates
    dup_mask = df.duplicated(subset=['Refined_Formal_Name'], keep=False)
    dupes = df[dup_mask].copy()
    
    if dupes.empty:
        print("No duplicates found based on Refined_Formal_Name.")
        return

    # Group by Refined_Formal_Name and aggregate
    summary = dupes.groupby('Refined_Formal_Name').agg({
        'Refined_Category': 'first', # Assuming category is consistent or taking first
        'Original_Entry': lambda x: ' | '.join(sorted(x.astype(str).unique())),
        'Status/Notes': lambda x: ' | '.join(sorted(x.astype(str).unique()))
    }).reset_index()
    
    # Add count column
    counts = dupes['Refined_Formal_Name'].value_counts().reset_index()
    counts.columns = ['Refined_Formal_Name', 'Count']
    
    summary = pd.merge(summary, counts, on='Refined_Formal_Name')
    summary = summary.sort_values('Count', ascending=False)
    
    # Reorder columns
    cols = ['Refined_Formal_Name', 'Count', 'Refined_Category', 'Original_Entry', 'Status/Notes']
    summary = summary[cols]

    # Save
    summary.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Duplicate summary saved to: {output_file}")
    print(f"Found {len(summary)} unique entities with duplicates.")
    
    # Print preview
    print("\n=== Duplicate Summary Preview (Top 20) ===")
    print(f"{'Name':<40} | {'Cnt':<3} | {'Variations (Original Entries)'}")
    print("-" * 100)
    for i, row in summary.head(20).iterrows():
        name = row['Refined_Formal_Name']
        if len(name) > 37: name = name[:37] + "..."
        variations = row['Original_Entry']
        if len(variations) > 50: variations = variations[:50] + "..."
        print(f"{name:<40} | {row['Count']:<3} | {variations}")

if __name__ == "__main__":
    generate_duplicate_summary()
