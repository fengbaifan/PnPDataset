import pandas as pd
import glob
import os
import re

input_dir = r'c:\Users\001\Desktop\14-Relation\06-Extraction-Rules'

def is_suspicious(text):
    if not isinstance(text, str):
        return False
    
    # Check for " and " which often indicates multiple entities
    if ' and ' in text:
        # Ignore common safe cases if any (e.g., "husband and wife" might be a single concept, but "A and B" is likely two)
        # We want to find things that SHOULD be split.
        return True
    
    # Check for comma lists, but try to avoid "Name, Title" or "City, Country"
    # A simple heuristic: multiple commas, or comma followed by "and"
    if text.count(',') > 1:
        # "City, Country" has 1 comma. "Name, Title" has 1 comma.
        # "A, B, and C" has 2+ commas.
        return True
        
    return False

def main():
    print(f"Scanning {input_dir}...", flush=True)
    files = glob.glob(os.path.join(input_dir, '*_Triples.csv'))
    print(f"Scanning {len(files)} files for suspicious entities...", flush=True)
    
    suspicious_count = 0
    
    for file_path in files:
        df = pd.read_csv(file_path)
        filename = os.path.basename(file_path)
        
        for idx, row in df.iterrows():
            subj = row['Subject']
            obj = row['Object']
            
            if is_suspicious(subj):
                print(f"[{filename}:{idx+2}] Suspicious Subject: {subj}")
                suspicious_count += 1
                
            if is_suspicious(obj):
                # Filter out some known patterns we already handle or are okay?
                # Actually, let's just see everything for now.
                print(f"[{filename}:{idx+2}] Suspicious Object:  {obj}")
                suspicious_count += 1

    print(f"Found {suspicious_count} suspicious entries.")

if __name__ == "__main__":
    main()
