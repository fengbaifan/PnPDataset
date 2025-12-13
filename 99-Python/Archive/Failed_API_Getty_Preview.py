import pandas as pd
import requests
import time
import os
import json

def search_getty_reconcile(term):
    endpoint = "http://vocab.getty.edu/reconcile"
    
    # Clean term
    term = term.replace('"', '').strip()
    
    # Construct query
    query = {"query": term}
        
    try:
        params = {'query': json.dumps(query)}
        # Add User-Agent just in case
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(endpoint, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('result', [])
        else:
            print(f"HTTP Error {response.status_code}")
            return None
    except Exception as e:
        print(f"Error querying for {term}: {e}")
        return None

def process_h_file():
    input_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\04-Index-Enrich\H_refined.csv'
    output_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\99-Python\02-Analysis\H_Getty_Preview.txt'
    
    df = pd.read_csv(input_file)
    
    print(f"Processing {len(df)} entries from {input_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Getty Vocabularies Search Results (via Reconciliation API) for {os.path.basename(input_file)}\n")
        f.write("="*80 + "\n\n")
        
        for index, row in df.iterrows():
            main_entry = row['Index_Main Entry']
            cidoc_type = row['CIDOC_Type']
            
            search_term = main_entry.strip().strip('"')
            
            print(f"Searching: {search_term} ({cidoc_type})...")
            f.write(f"Entry: {main_entry} (Type: {cidoc_type})\n")
            
            results = search_getty_reconcile(search_term)
            
            if results:
                for item in results[:3]: # Top 3 results
                    name = item.get('name')
                    score = item.get('score')
                    id = item.get('id')
                    types = item.get('type', [])
                    
                    f.write(f"  - Match: {name} (Score: {score})\n")
                    f.write(f"    ID: {id}\n")
                    f.write(f"    Types: {types}\n")
            else:
                f.write("  No results found.\n")
            
            f.write("-" * 40 + "\n")
            time.sleep(0.2)

    print(f"Done. Results saved to {output_file}")

if __name__ == "__main__":
    process_h_file()
