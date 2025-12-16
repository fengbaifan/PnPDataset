import pandas as pd
import os

input_file = r"09-QID-Crosscheck/04-Requery_Results_Advanced.csv"

def reorder_columns():
    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except:
        df = pd.read_csv(input_file, encoding='gbk')
        
    cols = df.columns.tolist()
    print("Current columns:", cols)
    
    # Define desired order
    # We want Second-Query_QID right after Original-QID
    
    if 'Original-QID' in cols and 'Second-Query_QID' in cols:
        # Remove Second-Query_QID from its current position
        cols.remove('Second-Query_QID')
        
        # Find index of Original-QID
        idx = cols.index('Original-QID')
        
        # Insert Second-Query_QID after Original-QID
        cols.insert(idx + 1, 'Second-Query_QID')
        
        print("New column order:", cols)
        
        df = df[cols]
        
        print(f"Saving to {input_file}...")
        df.to_csv(input_file, index=False, encoding='utf-8-sig')
        print("Done.")
    else:
        print("Error: Required columns not found.")

if __name__ == "__main__":
    reorder_columns()
