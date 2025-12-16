import pandas as pd
import os

input_file = r"09-QID-Crosscheck/03-Requery_Results.csv"

def fix_encoding():
    print(f"Reading {input_file} with GBK encoding...")
    try:
        df = pd.read_csv(input_file, encoding='gbk')
    except Exception as e:
        print(f"Failed to read with GBK: {e}")
        return

    print("Headers found:")
    print(df.columns.tolist())
    
    print("Saving with UTF-8-SIG encoding...")
    df.to_csv(input_file, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    fix_encoding()
