import pandas as pd
import os

input_file = r"09-QID-Crosscheck/04-Requery_Results_Advanced.csv"

def count_missing_qids():
    try:
        df = pd.read_csv(input_file)
    except:
        df = pd.read_csv(input_file, encoding='gbk')
        
    # Check for NaN or empty strings
    missing_mask = df['Second-Query_QID'].isna() | (df['Second-Query_QID'].astype(str).str.strip() == "")
    missing_count = missing_mask.sum()
    
    total_rows = len(df)
    print(f"Total Rows: {total_rows}")
    print(f"Missing Second-Query_QID: {missing_count}")
    print(f"Percentage Missing: {(missing_count/total_rows)*100:.2f}%")

if __name__ == "__main__":
    count_missing_qids()
