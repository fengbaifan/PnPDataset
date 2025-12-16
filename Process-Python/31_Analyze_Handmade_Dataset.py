import pandas as pd
import os

base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset\05-HandmadeDataset"
files = [
    "name-English_table.csv",
    "gio-English_table.csv",
    "work-English_table.csv"
]

def analyze_handmade_dataset():
    total_rows = 0
    all_entities = set()
    
    print(f"{'File':<30} | {'Rows':<10} | {'Unique Entities':<15}")
    print("-" * 60)

    for filename in files:
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            print(f"{filename:<30} | Not Found")
            continue
            
        try:
            # Try GBK first as seen in preview
            df = pd.read_csv(filepath, encoding='gbk')
        except:
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except:
                print(f"Could not read {filename}")
                continue
        
        rows = len(df)
        total_rows += rows
        
        # Identify name column
        # name/gio: 3rd column (index 2)
        # work: 2nd column (index 1)
        if 'name' in filename or 'gio' in filename:
            name_col = df.columns[2]
        else:
            name_col = df.columns[1]
            
        entities = df[name_col].dropna().unique()
        unique_count = len(entities)
        all_entities.update(entities)
        
        print(f"{filename:<30} | {rows:<10} | {unique_count:<15}")

    print("-" * 60)
    print(f"{'TOTAL':<30} | {total_rows:<10} | {len(all_entities):<15}")

if __name__ == "__main__":
    analyze_handmade_dataset()
