import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_csv = os.path.join(base_dir, "Process-Python", "02-Analysis", "Recheck_Duplicates_Full_List.csv")

def list_all_duplicates():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    # Find duplicates based on Refined_Formal_Name
    dup_names = df[df.duplicated(subset=['Refined_Formal_Name'], keep=False)]['Refined_Formal_Name'].unique()
    
    # Filter and sort
    dupes_df = df[df['Refined_Formal_Name'].isin(dup_names)].sort_values(by=['Refined_Formal_Name', 'Original_Entry'])
    
    # Select columns for clear display
    display_cols = ['Refined_Formal_Name', 'Refined_Category', 'Original_Entry', 'Status/Notes']
    final_df = dupes_df[display_cols]
    
    # Save to CSV
    final_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Full duplicate list saved to: {output_csv}")
    
    # Print all rows to terminal for user review
    print("\n=== Full List of Duplicates (Row by Row) ===")
    # Adjust pandas display options to show full content
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 100)
    
    # Iterate and print formatted
    current_group = ""
    for index, row in final_df.iterrows():
        group = row['Refined_Formal_Name']
        if group != current_group:
            print(f"\n--- {group} ({row['Refined_Category']}) ---")
            current_group = group
        print(f"  Original: {row['Original_Entry']:<50} | Note: {row['Status/Notes']}")

if __name__ == "__main__":
    list_all_duplicates()
