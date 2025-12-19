import pandas as pd
import os

def reorder_columns():
    file_path = r'09-QID-Crosscheck/06-Deep_Query_Results.csv'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    
    cols = df.columns.tolist()
    print("Original columns:", cols)
    
    target_col = 'Third-Query_QID'
    anchor_col = 'Second-Query_QID'
    
    if target_col in cols and anchor_col in cols:
        # Remove target from current position
        cols.remove(target_col)
        
        # Find anchor index
        anchor_idx = cols.index(anchor_col)
        
        # Insert target after anchor
        cols.insert(anchor_idx + 1, target_col)
        
        # Reorder dataframe
        df = df[cols]
        
        print("New column order:", cols)
        
        # Save back
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print("File saved successfully.")
    else:
        print(f"Columns {target_col} or {anchor_col} not found.")

if __name__ == "__main__":
    reorder_columns()
