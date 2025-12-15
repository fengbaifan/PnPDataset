import pandas as pd
import os
import csv
import re

def query_getty_for_audit_list():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    
    # Input/Output
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Combined.csv')
    output_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Getty_Matches.csv')
    
    # Getty Files
    ulan_file = os.path.join(base_dir, r'Getty\The Union List of Artist Names (ULAN)\ULANOut_Full.nt')
    tgn_file = os.path.join(base_dir, r'Getty\The Getty Thesaurus of Geographic Names (TGN)\TGNOut_Full.nt') # Corrected path based on previous list_dir
    aat_file = os.path.join(base_dir, r'Getty\The Art & Architecture Thesaurus (AAT)\AATOut_Full.nt') # Corrected path based on previous list_dir
    
    # Note: In previous turns, I noticed folder names might be swapped or confusing. 
    # Let's double check paths from previous `list_dir` output if needed.
    # Previous `list_dir` showed:
    # Getty/The Art & Architecture Thesaurus (AAT)/TGNOut_Full.nt  <-- TGN is in AAT folder?
    # Getty/The Getty Thesaurus of Geographic Names (TGN)/AATOut_Full.nt <-- AAT is in TGN folder?
    # Let's re-verify or use the paths that worked in 04_Query_Getty_B_Full.py
    
    # From 04_Query_Getty_B_Full.py content read previously:
    # ulan_file = ... ULANOut_Full.nt
    # tgn_file = ... Getty\The Art & Architecture Thesaurus (AAT)\TGNOut_Full.nt
    # aat_file = ... Getty\The Getty Thesaurus of Geographic Names (TGN)\AATOut_Full.nt
    # I will use these specific paths to be safe.
    
    tgn_file = os.path.join(base_dir, r'Getty\The Art & Architecture Thesaurus (AAT)\TGNOut_Full.nt')
    aat_file = os.path.join(base_dir, r'Getty\The Getty Thesaurus of Geographic Names (TGN)\AATOut_Full.nt')

    print(f"Loading targets from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Prepare targets
    # Structure: { 'normalized_name': { 'original_rows': [indices], 'type': 'ULAN'/'TGN'/'AAT' } }
    targets_by_dataset = {
        'ULAN': {},
        'TGN': {},
        'AAT': {}
    }
    
    for index, row in df.iterrows():
        reason = row.get('Extraction_Reason', '')
        
        target_name = ""
        dataset = "ULAN" # Default
        
        if 'Index' in reason:
            target_name = str(row.get('Index_Entry', '')).strip()
            c_type = str(row.get('CIDOC_Type', ''))
            
            if c_type == 'E53 Place':
                dataset = 'TGN'
            elif c_type in ['E21 Person', 'E74 Group']:
                dataset = 'ULAN'
            else:
                dataset = 'AAT'
                
        else: # Manual
            target_name = str(row.get('Manual_Name', '')).strip()
            file_code = str(row.get('File_Code', ''))
            
            if 'gio' in file_code.lower():
                dataset = 'TGN' # Places/Groups
            elif 'work' in file_code.lower():
                dataset = 'AAT'
            else:
                dataset = 'ULAN' # name-English
        
        # Clean name
        clean_name = target_name.strip().strip('"').strip("'")
        if not clean_name: continue
        
        # Add to targets
        if clean_name not in targets_by_dataset[dataset]:
            targets_by_dataset[dataset][clean_name] = []
        targets_by_dataset[dataset][clean_name].append(index)

    print(f"Targets loaded:")
    print(f"  ULAN: {len(targets_by_dataset['ULAN'])}")
    print(f"  TGN:  {len(targets_by_dataset['TGN'])}")
    print(f"  AAT:  {len(targets_by_dataset['AAT'])}")
    
    # Results storage
    # matches[index] = [ { 'id': '...', 'term': '...', 'dataset': '...' } ]
    matches = {} 

    def scan_file(filepath, target_dict, dataset_name):
        if not target_dict:
            print(f"Skipping {dataset_name} (no targets).")
            return

        print(f"Scanning {dataset_name} at {filepath}...")
        
        # Pre-compile regex or set for fast lookup
        # We look for literal matches of the name in the N-Triples
        # N-Triples format: <subject> <predicate> "object"@lang .
        # We want to match the "object" part.
        
        # Optimization: Create a set of target names for O(1) lookup
        target_set = set(target_dict.keys())
        
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    count += 1
                    if count % 5000000 == 0:
                        print(f"  Processed {count/1000000:.1f}M lines...")
                        
                    # Fast check: is any target in the line? 
                    # This is slow if we iterate all targets.
                    # Better: Extract the literal from the line and check if it's in target_set.
                    
                    # Line format usually: ... <...#label> "Name"@en .
                    if '"' not in line: continue
                    
                    try:
                        # Extract text between first and last quote (simplified)
                        # A safer way for N-Triples literals
                        start = line.find('"')
                        end = line.rfind('"')
                        if start == -1 or end == -1 or start >= end: continue
                        
                        literal = line[start+1:end]
                        
                        # Check exact match
                        if literal in target_set:
                            # Found a match!
                            # Extract ID
                            # Subject is usually <http://vocab.getty.edu/dataset/id>
                            parts = line.split(' ', 1)
                            subject = parts[0]
                            
                            # Extract numeric ID
                            # e.g. <http://vocab.getty.edu/ulan/500000833>
                            # or <http://vocab.getty.edu/ulan/term/1500002262> (Term ID, skip or map to Subject?)
                            # We prefer the main Subject ID (digits only usually)
                            
                            is_term = '/term/' in subject
                            
                            # We store this match
                            for idx in target_dict[literal]:
                                if idx not in matches: matches[idx] = []
                                
                                # Avoid duplicates
                                existing_ids = [m['id'] for m in matches[idx]]
                                if subject not in existing_ids:
                                    matches[idx].append({
                                        'id': subject,
                                        'term': literal,
                                        'dataset': dataset_name,
                                        'is_term': is_term
                                    })
                                    
                    except Exception:
                        continue
                        
        except FileNotFoundError:
            print(f"Error: File not found {filepath}")

    # Execute Scans
    scan_file(ulan_file, targets_by_dataset['ULAN'], 'ULAN')
    scan_file(tgn_file, targets_by_dataset['TGN'], 'TGN')
    scan_file(aat_file, targets_by_dataset['AAT'], 'AAT')
    
    # Write Results
    print("Writing results...")
    
    # Add columns to dataframe
    df['Getty_ID'] = ''
    df['Getty_Term'] = ''
    df['Getty_Dataset'] = ''
    
    match_count = 0
    
    for idx, match_list in matches.items():
        if not match_list: continue
        
        # Prioritize non-term IDs (Main Subject IDs)
        best_match = None
        for m in match_list:
            if not m['is_term']:
                best_match = m
                break
        
        if not best_match and match_list:
            best_match = match_list[0]
            
        if best_match:
            # Clean ID (remove < >)
            clean_id = best_match['id'].strip('<>')
            # Extract just the number if possible for cleaner CSV
            # http://vocab.getty.edu/ulan/500011508 -> 500011508
            if '/' in clean_id:
                short_id = clean_id.split('/')[-1]
            else:
                short_id = clean_id
                
            df.at[idx, 'Getty_ID'] = short_id
            df.at[idx, 'Getty_Term'] = best_match['term']
            df.at[idx, 'Getty_Dataset'] = best_match['dataset']
            match_count += 1
            
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Done. Found matches for {match_count} entries.")
    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    query_getty_for_audit_list()
