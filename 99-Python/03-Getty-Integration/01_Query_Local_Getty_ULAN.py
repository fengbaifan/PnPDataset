import pandas as pd
import os
import csv

def query_local_ulan():
    # Configuration
    ulan_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\Getty\The Union List of Artist Names (ULAN)\ULANOut_Full.nt'
    target_csv = r'c:\Users\001\Desktop\Github-Project\PnPDataset\04-Index-Enrich\H_refined.csv'
    output_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\99-Python\02-Analysis\H_Local_Getty_Results.txt'
    
    # 1. Load Target Names
    print(f"Loading targets from {target_csv}...")
    df = pd.read_csv(target_csv)
    # Clean names: remove quotes, extra spaces
    targets = set()
    for name in df['Index_Main Entry'].dropna():
        clean_name = name.strip().strip('"').strip("'")
        if clean_name:
            targets.add(clean_name)
    
    print(f"Looking for {len(targets)} unique names: {list(targets)[:5]}...")
    
    # 2. Scan ULAN File
    print(f"Scanning {ulan_file} (This may take a while)...")
    
    found_data = {name: [] for name in targets}
    
    try:
        with open(ulan_file, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = 0
            for line in f:
                line_count += 1
                if line_count % 1000000 == 0:
                    print(f"Processed {line_count/1000000:.1f}M lines...")
                
                # Optimization: Check if line contains any of the target names
                # This is still O(N*M) per line where M is num targets. 
                # Since M is small (~25), it's okay.
                # We look for the name enclosed in quotes to be safer, e.g. "Hogarth, William"
                
                for name in targets:
                    # Simple check: is the name in the line?
                    # We try to match literal format: "Name"
                    if f'"{name}"' in line:
                        found_data[name].append(line.strip())
                        
    except FileNotFoundError:
        print(f"Error: ULAN file not found at {ulan_file}")
        return

    # 3. Process and Save Results
    print("Processing results...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Local Getty ULAN Search Results for {os.path.basename(target_csv)}\n")
        f.write("="*80 + "\n\n")
        
        for name in sorted(targets):
            lines = found_data[name]
            f.write(f"Entry: {name}\n")
            if lines:
                f.write(f"  Found {len(lines)} matching triples:\n")
                # Extract ID from the first match if possible
                # Format: <http://vocab.getty.edu/ulan/ID> ...
                ids = set()
                for l in lines:
                    if l.startswith('<http://vocab.getty.edu/ulan/'):
                        parts = l.split('>')
                        if parts:
                            ids.add(parts[0] + '>')
                    
                    # Write the line (truncated if too long)
                    f.write(f"    {l[:200]}\n")
                
                if ids:
                    f.write(f"  Potential IDs: {', '.join(ids)}\n")
            else:
                f.write("  No matches found in ULAN.\n")
            f.write("-" * 40 + "\n")

    print(f"Done. Results saved to {output_file}")

if __name__ == "__main__":
    query_local_ulan()
