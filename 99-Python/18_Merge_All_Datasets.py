import pandas as pd
import os
import glob

def merge_datasets():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    dir_04 = os.path.join(base_dir, '04-Index-Enrich')
    dir_05 = os.path.join(base_dir, '05-HandmadeDataset')
    output_dir = os.path.join(base_dir, '08-Final-Dataset')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    all_data = []
    
    # --- Process 04: Index Dataset ---
    print("Processing 04-Index-Enrich...")
    files_04 = glob.glob(os.path.join(dir_04, '*_refined.csv'))
    
    for f in files_04:
        filename = os.path.basename(f)
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            
            # Standardize columns
            # We want: Entity_Name, Source, Original_File, Type, QID (if any), Extra_Info
            
            # Check if 'Index_Main Entry' exists
            if 'Index_Main Entry' not in df.columns:
                print(f"Skipping {filename}: 'Index_Main Entry' not found")
                continue
                
            temp_df = pd.DataFrame()
            temp_df['Entity_Name'] = df['Index_Main Entry']
            temp_df['Type'] = df.get('CIDOC_Type', '')
            temp_df['Source'] = 'Index'
            temp_df['Original_File'] = filename
            temp_df['QID'] = '' # Index dataset doesn't have QID in 04 usually, unless enriched? 
            # Actually 04 is "Enrich", but mostly location enrichment. 
            # If there are other useful columns, we can keep them.
            
            # Let's keep Page Numbers as Extra Info
            temp_df['Page_Numbers'] = df.get('Index_Page Numbers', '')
            
            all_data.append(temp_df)
            print(f"  Loaded {len(temp_df)} rows from {filename}")
            
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    # --- Process 05: Handmade Dataset ---
    print("\nProcessing 05-HandmadeDataset...")
    files_05 = ['name-English_table.csv', 'gio-English_table.csv', 'work-English_table.csv']
    
    type_map = {
        'name-English_table.csv': 'E21 Person',
        'gio-English_table.csv': 'E53 Place',
        'work-English_table.csv': 'E22 Man-Made Object'
    }
    
    for filename in files_05:
        f_path = os.path.join(dir_05, filename)
        if not os.path.exists(f_path):
            print(f"  File not found: {filename}")
            continue
            
        try:
            # Use GBK as discovered
            df = pd.read_csv(f_path, encoding='gbk')
            
            # Columns: QID, 数据来源, 统一英文全名
            if '统一英文全名' not in df.columns:
                print(f"Skipping {filename}: '统一英文全名' not found")
                continue
                
            temp_df = pd.DataFrame()
            temp_df['Entity_Name'] = df['统一英文全名']
            temp_df['Type'] = type_map.get(filename, 'Unknown')
            temp_df['Source'] = 'Handmade'
            temp_df['Original_File'] = filename
            temp_df['QID'] = df.get('QID', '')
            temp_df['Page_Numbers'] = '' # Handmade doesn't have page numbers usually
            
            all_data.append(temp_df)
            print(f"  Loaded {len(temp_df)} rows from {filename}")
            
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            
    # --- Merge and Save ---
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Clean Entity Name
        final_df['Entity_Name'] = final_df['Entity_Name'].astype(str).str.strip()
        final_df = final_df[final_df['Entity_Name'] != 'nan']
        final_df = final_df[final_df['Entity_Name'] != '']
        
        output_path = os.path.join(output_dir, 'Merged_All_Entities.csv')
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\nSuccessfully merged {len(final_df)} rows.")
        print(f"Saved to: {output_path}")
        
        # Print stats
        print("\nSource Distribution:")
        print(final_df['Source'].value_counts())
        
        print("\nType Distribution:")
        print(final_df['Type'].value_counts())
        
    else:
        print("No data found to merge.")

if __name__ == "__main__":
    merge_datasets()
