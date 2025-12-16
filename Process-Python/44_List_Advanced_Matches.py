import pandas as pd
import os

input_file = r"09-QID-Crosscheck/03-Requery_Results_Advanced.csv"

def list_new_matches():
    try:
        df = pd.read_csv(input_file)
    except:
        df = pd.read_csv(input_file, encoding='gbk')
        
    # Filter for rows where Logic indicates an "Advanced Match"
    # Our script set the logic string to start with "Advanced Match via..."
    
    mask = df['Second-Query_Logic'].astype(str).str.contains("Advanced Match", na=False)
    matches = df[mask]
    
    print(f"Total Advanced Matches: {len(matches)}")
    print("-" * 60)
    print(f"{'Original Name':<50} | {'Matched Label':<30} | {'QID':<10}")
    print("-" * 60)
    
    for _, row in matches.iterrows():
        orig = str(row['Refined_Formal_Name'])
        if len(orig) > 47: orig = orig[:47] + "..."
        
        matched = str(row['Second-Query_Label'])
        if len(matched) > 27: matched = matched[:27] + "..."
        
        qid = str(row['Second-Query_QID'])
        
        print(f"{orig:<50} | {matched:<30} | {qid:<10}")

if __name__ == "__main__":
    list_new_matches()
