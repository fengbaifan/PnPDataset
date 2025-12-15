import pandas as pd
import os

def extract_special_entries():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_file = os.path.join(base_dir, r'06-Crosscheck\Full_Comparison_Matrix_Unique.csv')
    output_file = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Combined.csv')
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Ensure Manual_QID is string and handle NaNs
    df['Manual_QID'] = df['Manual_QID'].fillna('').astype(str).str.strip()
    
    # Condition 1: Manual specific (Unmatched Manual AND Non-Q)
    cond_manual_target = (df['Status'] == 'Unmatched (Manual)') & \
                         (df['Manual_QID'] != '') & \
                         (~df['Manual_QID'].str.upper().str.startswith('Q'))
    
    # Condition 2: Index Unmatched
    cond_index_unmatched = df['Status'] == 'Unmatched (Index)'
    
    # Combine with OR (Union of the two sets of interest)
    combined_mask = cond_manual_target | cond_index_unmatched
    
    filtered_df = df[combined_mask].copy()
    
    # Add a 'Reason' column
    def get_reason(row):
        if row['Status'] == 'Unmatched (Index)':
            return 'Unmatched Index Entry'
        return 'Unmatched Manual & Non-Q ID'

    filtered_df['Extraction_Reason'] = filtered_df.apply(get_reason, axis=1)
    
    print(f"Total rows in source: {len(df)}")
    print(f"Rows matching 'Manual Target': {cond_manual_target.sum()}")
    print(f"Rows matching 'Index Unmatched': {cond_index_unmatched.sum()}")
    print(f"Total extracted rows: {len(filtered_df)}")
    
    filtered_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Saved extracted list to: {output_file}")

if __name__ == "__main__":
    extract_special_entries()
