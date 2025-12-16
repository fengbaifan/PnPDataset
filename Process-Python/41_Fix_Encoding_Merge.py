import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file_02 = os.path.join(base_dir, "09-QID-Crosscheck", "02-Merged_Recheck_With_QID_Cleaned.csv")
input_file_03 = os.path.join(base_dir, "09-QID-Crosscheck", "03-Requery_Results.csv")
output_file = os.path.join(base_dir, "09-QID-Crosscheck", "03-Requery_Results_Fixed.csv")

def fix_encoding_issues():
    print("Starting encoding repair...")
    
    # 1. Load the clean source (02) which we know has correct characters like 'č'
    print(f"Loading source file: {input_file_02}")
    try:
        df_source = pd.read_csv(input_file_02, encoding='utf-8-sig')
    except:
        print("Warning: Could not read source with utf-8-sig, trying utf-8")
        df_source = pd.read_csv(input_file_02, encoding='utf-8')
        
    # 2. Load the results file (03) which has the query results but might have garbled names
    print(f"Loading results file: {input_file_03}")
    try:
        df_results = pd.read_csv(input_file_03, encoding='utf-8-sig')
    except:
        df_results = pd.read_csv(input_file_03, encoding='gbk') # It might have been saved as GBK/UTF-8 mixed

    print(f"Source rows: {len(df_source)}")
    print(f"Result rows: {len(df_results)}")
    
    if len(df_source) != len(df_results):
        print("Error: Row counts do not match. Cannot safely merge.")
        return

    # 3. Restore the correct Name and Category from Source
    # We trust the query results (QID, Label, Desc, Logic) but not the Name/Category columns in 03
    
    # Create a new dataframe starting with source columns
    df_fixed = df_source.copy()
    
    # Rename source columns to match expected output format if needed
    # 02 has: Refined_Formal_Name, QID, Refined_Category, Status/Notes
    # 03 has: Refined_Formal_Name, Original-QID, Second-Query_QID, ...
    
    # Map 02 columns to 03 schema
    df_fixed = df_fixed.rename(columns={
        'QID': 'Original-QID',
        'Refined_Category': 'Original-Refined_Category',
        'Status/Notes': 'Original-Status/Notes'
    })
    
    # Copy the query results from 03 to the fixed dataframe
    # Assuming row order is preserved (it should be as we just iterated)
    df_fixed['Second-Query_QID'] = df_results['Second-Query_QID']
    df_fixed['Second-Query_Label'] = df_results['Second-Query_Label']
    df_fixed['Second-Query_Description'] = df_results['Second-Query_Description']
    df_fixed['Second-Query_Logic'] = df_results['Second-Query_Logic']
    
    # 4. Re-check for specific known issues (like the '?' in Poreč)
    # If the query failed because of the bad name, we might need to re-query those specific rows.
    # Let's identify rows where the name in 03 had '?' but 02 didn't.
    
    issues_count = 0
    for idx, row in df_fixed.iterrows():
        original_name = row['Refined_Formal_Name']
        bad_name = df_results.iloc[idx]['Refined_Formal_Name']
        
        # Simple check: if lengths differ significantly or '?' appears in bad but not original
        if str(bad_name) != str(original_name):
            # If the query logic says "No results found", it might be due to the bad name
            if "No results found" in str(row['Second-Query_Logic']):
                issues_count += 1
                # We could mark this for re-query, or just leave it fixed for now.
                # For this script, we just fix the text. Re-querying would require the API.
    
    print(f"Restored correct names for {len(df_fixed)} rows.")
    print(f"Found {issues_count} rows where name corruption might have caused search failure.")
    
    # 5. Save
    print(f"Saving fixed file to {output_file}...")
    df_fixed.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # Overwrite the original 03 file to avoid confusion?
    # os.replace(output_file, input_file_03)
    # print(f"Overwrote {input_file_03}")
    
    print("Done.")

if __name__ == "__main__":
    fix_encoding_issues()
