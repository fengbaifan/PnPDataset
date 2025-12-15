import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_report = os.path.join(base_dir, "Duplicate_Rows_Report.txt")

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

    with open(output_report, 'w', encoding='utf-8') as f:
        header = f"=== Full List of Duplicate Rows ({len(dupes)} rows) ===\n"
        f.write(header)
        print(header.strip())
        
        header_cols = f"{'Refined_Formal_Name':<40} | {'Original_Entry':<40} | {'Note'}\n"
        f.write(header_cols)
        print(header_cols.strip())
        
        separator = "-" * 100 + "\n"
        f.write(separator)
        print(separator.strip())
        
        current_name = ""
        for index, row in dupes.iterrows():
            name = str(row['Refined_Formal_Name'])
            original = str(row['Original_Entry'])
            note = str(row['Status/Notes'])
            
            # Truncate for display/file to keep it tabular
            display_name = name[:37] + "..." if len(name) > 37 else name
            display_original = original[:37] + "..." if len(original) > 37 else original
            display_note = note[:20] + "..." if len(note) > 20 else note
            
            if row['Refined_Formal_Name'] != current_name:
                if current_name != "":
                    f.write(separator)
                    print(separator.strip())
                current_name = row['Refined_Formal_Name']
                
            line = f"{display_name:<40} | {display_original:<40} | {display_note}\n"
            f.write(line)
            print(line.strip())

    print(f"\nReport saved to: {output_report}")

if __name__ == "__main__":
    list_all_duplicate_rows()
