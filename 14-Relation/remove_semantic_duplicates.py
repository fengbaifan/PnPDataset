import pandas as pd
import os

input_file = r'c:\Users\001\Desktop\14-Relation\07-Merged-Data\All_Triples_Merged.csv'
output_file = r'c:\Users\001\Desktop\14-Relation\07-Merged-Data\All_Triples_Merged_Unique.csv'

def main():
    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    total_rows = len(df)
    print(f"Total rows: {total_rows}")

    # Remove semantic duplicates (same Subject, Predicate, Object)
    # We keep the first occurrence.
    # We might want to aggregate Source_Raw or something? 
    # For now, let's just keep the first one as usually requested for unique triples.
    
    subset_cols = ['Subject', 'Predicate', 'Object']
    df_unique = df.drop_duplicates(subset=subset_cols)
    
    unique_rows = len(df_unique)
    removed_count = total_rows - unique_rows
    
    print(f"Rows after removing semantic duplicates: {unique_rows}")
    print(f"Removed {removed_count} duplicates.")
    
    print(f"Saving to {output_file}...")
    df_unique.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    main()
