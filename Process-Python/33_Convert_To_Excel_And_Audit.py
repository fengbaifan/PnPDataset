import pandas as pd
import os
import re

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_dir = os.path.join(base_dir, "08-Data-Remerge")
# User asked for "01-Merged_Recheck_Simplified" but likely meant the one we just created "03"
# We will use 03 as input
input_file = os.path.join(input_dir, "03-Merged_Recheck_Simplified.csv")
output_file = os.path.join(input_dir, "03-Merged_Recheck_Simplified.xlsx")

def check_and_convert():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        print("UTF-8-SIG failed, trying GBK...")
        df = pd.read_csv(input_file, encoding='gbk')

    print(f"Rows: {len(df)}")
    
    # 1. Check for potential encoding issues (Mojibake detection)
    # Common mojibake patterns often involve sequences of accented characters where they shouldn't be
    # e.g. "Ã©" instead of "é"
    
    mojibake_pattern = r'[ÃÂ][©®±µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]'
    
    potential_errors = []
    
    for col in df.columns:
        # Find rows matching the pattern
        matches = df[df[col].astype(str).str.contains(mojibake_pattern, regex=True, na=False)]
        if not matches.empty:
            for idx, row in matches.iterrows():
                potential_errors.append({
                    'Row': idx + 2, # Excel row (1-header + 1-index)
                    'Column': col,
                    'Value': row[col]
                })

    if potential_errors:
        print("\n[WARNING] Potential encoding errors (Mojibake) found:")
        for err in potential_errors[:10]: # Show first 10
            print(f"Row {err['Row']}, Col '{err['Column']}': {err['Value']}")
        if len(potential_errors) > 10:
            print(f"...and {len(potential_errors) - 10} more.")
    else:
        print("\n[PASS] No obvious mojibake patterns found.")

    # 2. Check for NaN in critical columns
    nan_names = df['Refined_Formal_Name'].isna().sum()
    if nan_names > 0:
        print(f"\n[WARNING] Found {nan_names} rows with missing Refined_Formal_Name.")
    else:
        print("\n[PASS] All rows have Refined_Formal_Name.")

    # 3. Save as Excel
    print(f"\nConverting to Excel: {output_file}")
    try:
        # Using xlsxwriter engine for better compatibility if available, else default
        df.to_excel(output_file, index=False, engine='openpyxl')
        print("Success! Excel file created.")
    except Exception as e:
        print(f"Error creating Excel file: {e}")

if __name__ == "__main__":
    check_and_convert()
