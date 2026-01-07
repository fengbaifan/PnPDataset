import pandas as pd
import glob
import os

input_dir = r'c:\Users\001\Desktop\14-Relation\06-Extraction-Rules'
output_dir = r'c:\Users\001\Desktop\14-Relation\07-Merged-Data'
output_file = os.path.join(output_dir, 'All_Triples_Merged.csv')

def main():
    print(f"Scanning {input_dir}...")
    files = glob.glob(os.path.join(input_dir, '*_Triples.csv'))
    print(f"Found {len(files)} files to merge.")
    
    all_dfs = []
    total_rows = 0
    
    for file_path in files:
        print(f"Reading {os.path.basename(file_path)}...")
        try:
            df = pd.read_csv(file_path)
            # Add a column for source file, might be useful
            # df['Source_File'] = os.path.basename(file_path)
            all_dfs.append(df)
            total_rows += len(df)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    if all_dfs:
        print("Concatenating...")
        merged_df = pd.concat(all_dfs, ignore_index=True)
        
        # Ensure columns are in standard order if needed, but usually concat handles it.
        # Clean up any potential 'Unnamed' columns
        merged_df = merged_df.loc[:, ~merged_df.columns.str.contains('^Unnamed')]
        
        print(f"Total rows read: {total_rows}")
        print(f"Total rows in merged: {len(merged_df)}")
        
        print(f"Saving to {output_file}...")
        merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print("Done.")
    else:
        print("No data found.")

if __name__ == "__main__":
    main()
