import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")

def check_duplicates_by_name():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    # 1. Count occurrences of each Refined_Formal_Name
    name_counts = df['Refined_Formal_Name'].value_counts()
    
    # 2. Filter for those appearing more than once
    duplicate_names = name_counts[name_counts > 1]
    
    print(f"\n=== Duplicate Check Report (Based ONLY on Refined_Formal_Name) ===")
    print(f"Total Unique Names: {len(name_counts)}")
    print(f"Names with Duplicates: {len(duplicate_names)}")
    print(f"Total Rows involved in Duplicates: {duplicate_names.sum()}")
    print("-" * 60)
    
    # 3. Display the duplicates with their counts
    print(f"{'Refined_Formal_Name':<50} | {'Count':<5}")
    print("-" * 60)
    
    # Convert to dataframe for easier printing
    dupes_summary = duplicate_names.reset_index()
    dupes_summary.columns = ['Refined_Formal_Name', 'Count']
    
    # Print top 50 most frequent duplicates
    for index, row in dupes_summary.head(50).iterrows():
        print(f"{row['Refined_Formal_Name']:<50} | {row['Count']:<5}")
    
    if len(dupes_summary) > 50:
        print(f"... and {len(dupes_summary) - 50} more.")

    # 4. (Optional) Show the detailed rows for the top 5 duplicates to illustrate
    print("\n=== Detail View (Top 5 Duplicated Names) ===")
    top_5_names = dupes_summary.head(5)['Refined_Formal_Name'].tolist()
    details = df[df['Refined_Formal_Name'].isin(top_5_names)].sort_values('Refined_Formal_Name')
    
    for name in top_5_names:
        print(f"\nName: {name}")
        rows = details[details['Refined_Formal_Name'] == name]
        for idx, row in rows.iterrows():
            print(f"  - Row {idx+1}: {row['Original_Entry']} (Category: {row['Refined_Category']})")

if __name__ == "__main__":
    check_duplicates_by_name()
