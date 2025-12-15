import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_report = os.path.join(base_dir, "Process-Python", "02-Analysis", "Recheck_Duplicates_Report.txt")

def inspect_duplicates():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    # Find duplicates based on Refined_Formal_Name
    # We want to see ALL entries for names that appear more than once
    dup_names = df[df.duplicated(subset=['Refined_Formal_Name'], keep=False)]['Refined_Formal_Name'].unique()
    
    print(f"Found {len(dup_names)} unique entities with multiple entries.")
    
    # Filter the dataframe to only include these duplicates
    dupes_df = df[df['Refined_Formal_Name'].isin(dup_names)].sort_values(by=['Refined_Formal_Name', 'Original_Entry'])
    
    report_lines = []
    report_lines.append("=== Recheck Duplicates Inspection ===")
    report_lines.append(f"Total Unique Entities with Duplicates: {len(dup_names)}")
    report_lines.append(f"Total Rows involved: {len(dupes_df)}")
    report_lines.append("-" * 50)

    current_name = None
    for index, row in dupes_df.iterrows():
        name = row['Refined_Formal_Name']
        original = row['Original_Entry']
        category = row['Refined_Category']
        note = str(row['Status/Notes']).strip()
        
        if name != current_name:
            report_lines.append(f"\n> {name} [{category}]")
            current_name = name
        
        report_lines.append(f"    - Original: {original:<40} | Note: {note}")

    # Save Report
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report saved to: {output_report}")
    
    # Print the first few examples to terminal
    print("\n--- Preview of Top 5 Duplicated Groups ---")
    count = 0
    for line in report_lines:
        if line.startswith(">"):
            count += 1
        if count > 5:
            break
        print(line)

if __name__ == "__main__":
    inspect_duplicates()
