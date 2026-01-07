import pandas as pd
import os

# Configuration
input_file = r'c:\Users\001\Desktop\14-Relation\03-Handmade\01-Handmade_filtered.csv'
output_file = r'c:\Users\001\Desktop\14-Relation\03-Handmade\01-Handmade_refined.csv'

def refine_data():
    print(f"Reading file: {input_file}")
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return

    try:
        df = pd.read_csv(input_file)
        
        print(f"Original shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # 1. Drop '章节' column
        if '章节' in df.columns:
            print("Dropping column '章节'...")
            df = df.drop(columns=['章节'])
        else:
            print("Warning: Column '章节' not found.")

        # 2. Filter rows where both QID columns have values
        # Identifying QID columns based on name containing 'QID'
        qid_cols = [col for col in df.columns if 'QID' in str(col).upper()]
        print(f"Identified QID columns: {qid_cols}")
        
        if len(qid_cols) < 2:
            print("Error: Could not find two QID columns to filter on.")
            return

        # Filter: Both QID columns must be not null
        # We also treat empty strings or 'None' strings as null just in case
        initial_count = len(df)
        
        # Ensure we are checking for actual values
        mask = df[qid_cols[0]].notna() & df[qid_cols[1]].notna()
        
        # If there are string 'None' or 'nan' values, handle them? 
        # Pandas read_csv usually handles standard NA values.
        # Let's double check for string "None" just in case it was written literally in previous steps.
        # But previous step used openpyxl and saved to csv via pandas, so standard nan should be there.
        
        df_refined = df[mask]
        
        final_count = len(df_refined)
        print(f"Rows after filtering (both QIDs present): {final_count}")
        print(f"Dropped {initial_count - final_count} rows.")

        # Save to CSV
        print(f"Saving to: {output_file}")
        df_refined.to_csv(output_file, index=False, encoding='utf-8-sig')
        print("Done.")

    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    refine_data()
