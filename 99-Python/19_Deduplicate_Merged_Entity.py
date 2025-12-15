import pandas as pd
import os

def deduplicate_entities():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    # Folder name seems to be 08-EntityMerge based on previous rename? 
    # Wait, user asked to rename 08-Final-Dataset to EntityMerge.
    # But list_dir shows 08-EntityMerge? 
    # Ah, I might have renamed it to "08-EntityMerge" or just "EntityMerge"?
    # Let's check the list_dir output again. It says "08-EntityMerge".
    # Wait, the previous rename command was: Rename-Item ... -NewName "EntityMerge"
    # But maybe I manually added 08- prefix or the system did?
    # Let's look at the list_dir output: "08-EntityMerge/"
    # So the folder is named "08-EntityMerge".
    
    input_csv = os.path.join(base_dir, r'08-EntityMerge\01-Merged_All_Entities.csv')
    mapping_csv = os.path.join(base_dir, r'06-Crosscheck\Full_Comparison_Matrix_Unique.csv')
    output_csv = os.path.join(base_dir, r'08-EntityMerge\02-Deduplicated_Entities.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    print(f"Original rows: {len(df)}")
    
    # 1. Load Mapping to normalize names
    # We want to convert Index Names to Manual Names if they are matched
    print(f"Loading mapping from {mapping_csv}...")
    if os.path.exists(mapping_csv):
        map_df = pd.read_csv(mapping_csv)
        # Filter for Matched rows
        matched_df = map_df[map_df['Status'] == 'Matched']
        # Create dictionary: Index_Entry -> Manual_Name
        # Note: Index_Entry in mapping might be quoted differently, need to be careful?
        # In 04-Index-Enrich, names were cleaned. In Matrix, they usually match.
        # Let's assume direct string match works for now.
        index_to_manual = dict(zip(matched_df['Index_Entry'], matched_df['Manual_Name']))
        print(f"Loaded {len(index_to_manual)} mappings.")
        
        # Apply mapping
        # Only apply to rows where Source is 'Index'
        def normalize_name(row):
            if row['Source'] == 'Index':
                name = row['Entity_Name']
                if name in index_to_manual:
                    return index_to_manual[name]
            return row['Entity_Name']
            
        df['Normalized_Name'] = df.apply(normalize_name, axis=1)
    else:
        print("Mapping file not found. Proceeding with exact string deduplication only.")
        df['Normalized_Name'] = df['Entity_Name']

    # 2. Aggregation Logic
    # We group by 'Normalized_Name'
    
    def aggregate_group(group):
        # Type: Prefer Manual Type (E21 Person etc), else take first non-empty
        types = group['Type'].dropna().unique()
        # Heuristic: If 'E21 Person' is in there, take it.
        final_type = types[0] if len(types) > 0 else ''
        
        # Source: Join unique
        sources = group['Source'].dropna().unique()
        final_source = ' + '.join(sorted(sources))
        
        # QID: Take first non-empty
        qids = group['QID'].dropna().astype(str)
        qids = qids[qids != '']
        qids = qids[qids != 'nan']
        final_qid = qids.iloc[0] if len(qids) > 0 else ''
        
        # Page Numbers: Join unique
        pages = group['Page_Numbers'].dropna().astype(str)
        pages = pages[pages != '']
        pages = pages[pages != 'nan']
        # Split by comma if multiple pages in one cell?
        # Simple join for now
        final_pages = '; '.join(sorted(set(pages)))
        
        # Original File
        files = group['Original_File'].dropna().unique()
        final_files = '; '.join(sorted(files))
        
        return pd.Series({
            'Entity_Name': group['Normalized_Name'].iloc[0], # Use the normalized name
            'Type': final_type,
            'Source': final_source,
            'QID': final_qid,
            'Page_Numbers': final_pages,
            'Original_Files': final_files,
            'Original_Count': len(group)
        })

    print("Deduplicating...")
    deduped_df = df.groupby('Normalized_Name').apply(aggregate_group).reset_index(drop=True)
    
    print(f"Deduplicated rows: {len(deduped_df)}")
    
    # Save
    deduped_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved to {output_csv}")

if __name__ == "__main__":
    deduplicate_entities()
