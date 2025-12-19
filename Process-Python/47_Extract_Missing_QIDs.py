import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "09-QID-Crosscheck", "04-Requery_Results_Advanced.csv")
output_file = os.path.join(base_dir, "09-QID-Crosscheck", "05-Missing_QID_Report.csv")

def extract_missing():
    print(f"Loading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except:
        df = pd.read_csv(input_file, encoding='gbk')
        
    # Filter for missing Second-Query_QID
    mask = df['Second-Query_QID'].isna() | (df['Second-Query_QID'].astype(str).str.strip() == "")
    missing_df = df[mask]
    
    count = len(missing_df)
    print(f"Found {count} rows with missing QIDs.")
    
    print(f"Saving to {output_file}...")
    missing_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    extract_missing()
