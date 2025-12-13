import pandas as pd
import os
import csv

def query_getty_datasets():
    # Configuration - Note the folder swap correction
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    
    # ULAN is in ULAN folder
    ulan_file = os.path.join(base_dir, r'Getty\The Union List of Artist Names (ULAN)\ULANOut_Full.nt')
    
    # TGN is in AAT folder (based on previous list_dir)
    tgn_file = os.path.join(base_dir, r'Getty\The Art & Architecture Thesaurus (AAT)\TGNOut_Full.nt')
    
    # AAT is in TGN folder (based on previous list_dir)
    aat_file = os.path.join(base_dir, r'Getty\The Getty Thesaurus of Geographic Names (TGN)\AATOut_Full.nt')
    
    input_csv = os.path.join(base_dir, r'04-Index-Enrich\B_refined.csv')
    output_file = os.path.join(base_dir, r'99-Python\02-Analysis\B_Getty_Full_Results.txt')
    
    # 1. Load and Categorize Targets
    print(f"Loading targets from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    ulan_targets = set()
    tgn_targets = set()
    aat_targets = set()
    
    for index, row in df.iterrows():
        name = row['Index_Main Entry'].strip().strip('"').strip("'")
        c_type = row['CIDOC_Type']
        
        if not name: continue
        
        if c_type in ['E21 Person', 'E74 Group']:
            ulan_targets.add(name)
        elif c_type == 'E53 Place':
            tgn_targets.add(name)
        else: # E22, E28, E5 -> AAT
            aat_targets.add(name)
            
    print(f"Targets loaded:")
    print(f"  ULAN (Person/Group): {len(ulan_targets)}")
    print(f"  TGN (Place): {len(tgn_targets)}")
    print(f"  AAT (Object/Concept): {len(aat_targets)}")
    
    results = {} # Key: Name, Value: List of matching lines

    # Helper function to scan a file
    def scan_file(filepath, targets, dataset_name):
        print(f"Scanning {dataset_name} at {filepath}...")
        if not os.path.exists(filepath):
            print(f"  Error: File not found: {filepath}")
            return

        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    count += 1
                    if count % 5000000 == 0:
                        print(f"  Processed {count/1000000:.1f}M lines...")
                    
                    # Optimization: Check for literal string match first
                    # We look for "Name" to avoid partial matches inside other words if possible, 
                    # but simple substring is faster for this scale than regex
                    for name in targets:
                        if f'"{name}"' in line:
                            if name not in results: results[name] = []
                            results[name].append(f"[{dataset_name}] {line.strip()}")
        except Exception as e:
            print(f"  Error reading file: {e}")

    # 2. Execute Scans
    # Scan ULAN
    if ulan_targets:
        scan_file(ulan_file, ulan_targets, "ULAN")
        
    # Scan TGN
    if tgn_targets:
        scan_file(tgn_file, tgn_targets, "TGN")
        
    # Scan AAT
    if aat_targets:
        scan_file(aat_file, aat_targets, "AAT")

    # 3. Write Results
    print("Writing results...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Getty Datasets Search Results for {os.path.basename(input_csv)}\n")
        f.write("="*80 + "\n\n")
        
        # Write in alphabetical order of names
        all_names = sorted(list(ulan_targets | tgn_targets | aat_targets))
        
        for name in all_names:
            # Determine original type for label
            c_type = "Unknown"
            if name in ulan_targets: c_type = "Person/Group (ULAN Target)"
            elif name in tgn_targets: c_type = "Place (TGN Target)"
            elif name in aat_targets: c_type = "Object/Concept (AAT Target)"
            
            f.write(f"Entry: {name} ({c_type})\n")
            
            if name in results and results[name]:
                f.write(f"  Found {len(results[name])} matches:\n")
                
                # Extract potential IDs
                ids = set()
                for line in results[name]:
                    # Try to grab the subject URI
                    if line.startswith('['):
                        # [Dataset] <http://...
                        parts = line.split(' ')
                        if len(parts) > 1 and parts[1].startswith('<http'):
                            ids.add(parts[1])
                
                if ids:
                    f.write(f"  Potential IDs: {', '.join(list(ids)[:5])}\n")
                
                # Print first 10 matches to save space
                for i, line in enumerate(results[name]):
                    if i >= 10:
                        f.write(f"    ... and {len(results[name]) - 10} more lines.\n")
                        break
                    f.write(f"    {line[:200]}\n")
            else:
                f.write("  No matches found.\n")
            
            f.write("-" * 40 + "\n")

    print(f"Done. Report saved to {output_file}")

if __name__ == "__main__":
    query_getty_datasets()
