import pandas as pd
import os

input_file = r'c:\Users\001\Desktop\14-Relation\07-Merged-Data\All_Triples_Merged.csv'
output_file = r'c:\Users\001\Desktop\14-Relation\07-Merged-Data\All_Triples_Merged_NoDup.csv'

def main():
    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    total_rows = len(df)
    print(f"Total rows: {total_rows}")

    # Check for exact duplicates (all columns)
    duplicates = df[df.duplicated(keep=False)]
    duplicate_count = len(duplicates)
    
    # Check for duplicates based on Subject, Predicate, Object (ignoring Source_Raw/QIDs if they differ but content is same)
    # Actually, if Source_Raw differs, maybe we want to keep them? 
    # Usually in KG, (S, P, O) is the unique key.
    
    subset_cols = ['Subject', 'Predicate', 'Object']
    semantic_duplicates = df[df.duplicated(subset=subset_cols, keep=False)]
    semantic_dup_count = len(semantic_duplicates)

    print(f"\nExact duplicates (all columns): {duplicate_count}")
    if duplicate_count > 0:
        print(duplicates.head(10))

    print(f"\nSemantic duplicates (Subject, Predicate, Object): {semantic_dup_count}")
    if semantic_dup_count > 0:
        print(semantic_duplicates.sort_values(by=subset_cols).head(20))

    # Remove exact duplicates
    if duplicate_count > 0:
        print("\nRemoving exact duplicates...")
        df_nodup = df.drop_duplicates()
        print(f"Rows after removing exact duplicates: {len(df_nodup)}")
        
        # Determine if we should also remove semantic duplicates?
        # Let's start with just saving the one without exact duplicates.
        # If user wants to merge sources for semantic duplicates, that's a different task.
        # But usually duplicate triples are just noise.
        
        # Let's remove duplicates based on S, P, O and keep the first one?
        # Or keep all unique sources?
        # For now, let's just do exact duplicates.
        
        df_nodup.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Saved cleaned file to {output_file}")
        
        # Overwrite original?
        # print("Overwriting original file...")
        # df_nodup.to_csv(input_file, index=False, encoding='utf-8-sig')
    else:
        print("\nNo exact duplicates found.")

if __name__ == "__main__":
    main()
