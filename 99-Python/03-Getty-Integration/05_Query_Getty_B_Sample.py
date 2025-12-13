import pandas as pd
import os
import csv

# Configuration
base_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
csv_path = os.path.join(base_path, "04-Index-Enrich", "B_refined.csv")
output_path = os.path.join(base_path, "99-Python", "02-Analysis", "B_Getty_Sample_Results.txt")

# Corrected Paths based on directory listing
ulan_path = os.path.join(base_path, "Getty", "The Union List of Artist Names (ULAN)", "ULANOut_Full.nt")
# TGN is in AAT folder
tgn_path = os.path.join(base_path, "Getty", "The Art & Architecture Thesaurus (AAT)", "TGNOut_Full.nt")
# AAT is in TGN folder
aat_path = os.path.join(base_path, "Getty", "The Getty Thesaurus of Geographic Names (TGN)", "AATOut_Full.nt")

# Load CSV
df = pd.read_csv(csv_path)
targets = df[['Index_Main Entry', 'CIDOC_Type']].drop_duplicates().head(10) # Limit to top 10 for speed

print(f"Processing {len(targets)} targets from B_refined.csv (Sample Run)")

results = []

def search_file(file_path, search_terms, dataset_name):
    print(f"Scanning {dataset_name}...")
    found = {}
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return found
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i % 1000000 == 0 and i > 0:
                    print(f"  Scanned {i/1000000:.1f}M lines...")
                
                # Optimization: Check if line contains any of the search terms
                # This is still slow for many terms, but for 10 it's okay
                for term in search_terms:
                    if f'"{term}"' in line: # Simple string match with quotes to avoid partials
                        if term not in found:
                            found[term] = []
                        found[term].append(line.strip())
                        
                # Break early if we found everything (unlikely for triples but good for existence)
                # For this sample, we want all triples, so we scan full file? 
                # Scanning 10GB takes time. 
                # Let's limit scan to first 5M lines for this demo if possible, 
                # or just accept it takes a minute.
                if i > 5000000: # Limit to 5 Million lines for speed in this demo
                    print("  Reached 5M line limit for sample.")
                    break
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return found

# Group targets by dataset
ulan_terms = targets[targets['CIDOC_Type'].isin(['E21 Person', 'E74 Group', 'E39 Actor'])]['Index_Main Entry'].tolist()
tgn_terms = targets[targets['CIDOC_Type'] == 'E53 Place']['Index_Main Entry'].tolist()
aat_terms = targets[targets['CIDOC_Type'].isin(['E22 Man-Made Object', 'E28 Conceptual Object', 'E55 Type'])]['Index_Main Entry'].tolist()

# Clean terms (remove quotes if present in CSV string, though pandas handles this)
ulan_terms = [t.replace('"', '') for t in ulan_terms]
tgn_terms = [t.replace('"', '') for t in tgn_terms]
aat_terms = [t.replace('"', '') for t in aat_terms]

print(f"ULAN Terms: {ulan_terms}")
print(f"TGN Terms: {tgn_terms}")
print(f"AAT Terms: {aat_terms}")

# Execute Searches
all_findings = {}

if ulan_terms:
    all_findings.update(search_file(ulan_path, ulan_terms, "ULAN"))

if tgn_terms:
    all_findings.update(search_file(tgn_path, tgn_terms, "TGN"))

if aat_terms:
    all_findings.update(search_file(aat_path, aat_terms, "AAT"))

# Write Results
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("Getty Enrichment Sample Results (Top 10 from B_refined.csv)\n")
    f.write("=========================================================\n\n")
    
    for term in targets['Index_Main Entry']:
        clean_term = term.replace('"', '')
        f.write(f"Entity: {clean_term}\n")
        f.write(f"Type: {targets[targets['Index_Main Entry'] == term]['CIDOC_Type'].values[0]}\n")
        
        if clean_term in all_findings:
            f.write("Matches found:\n")
            for line in all_findings[clean_term]:
                f.write(f"  {line}\n")
        else:
            f.write("  No matches found in first 5M lines.\n")
        f.write("\n---------------------------------------------------------\n\n")

print(f"Done. Results written to {output_path}")
