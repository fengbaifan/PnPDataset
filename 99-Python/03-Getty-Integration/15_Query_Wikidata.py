import pandas as pd
import requests
import time
import os
import json

def search_wikidata(query, limit=5):
    """
    Searches Wikidata for a given query string.
    Returns a list of results (dicts with id, label, description).
    """
    if not query or pd.isna(query):
        return []
        
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": query,
        "limit": limit,
        "type": "item"
    }
    
    try:
        # User-Agent is required by Wikidata policy
        headers = {
            'User-Agent': 'PnPDatasetBot/1.0 (mailto:your_email@example.com)'
        }
        
        # Retry logic
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("search", [])
                elif response.status_code == 429:
                    # Too many requests, wait longer
                    time.sleep(5)
                    continue
                else:
                    print(f"Error: {response.status_code} for {query}")
                    return []
            except requests.exceptions.RequestException as e:
                print(f"Network error on attempt {attempt+1} for {query}: {e}")
                time.sleep(2)
                continue
                
        return []
            
    except Exception as e:
        print(f"Exception searching {query}: {e}")
        return []

def process_audit_list():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Normalized_Full.csv')
    output_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Wikidata_Enriched.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Add new columns if they don't exist
    if 'Wikidata_QID' not in df.columns:
        df['Wikidata_QID'] = ''
    if 'Wikidata_Label' not in df.columns:
        df['Wikidata_Label'] = ''
    if 'Wikidata_Description' not in df.columns:
        df['Wikidata_Description'] = ''
    if 'Wikidata_Candidates' not in df.columns:
        df['Wikidata_Candidates'] = ''

    total_rows = len(df)
    print(f"Processing {total_rows} rows...")
    
    # We will save progress every 50 rows
    for index, row in df.iterrows():
        # Skip if already processed (if re-running)
        if pd.notna(row['Wikidata_QID']) and row['Wikidata_QID'] != '':
            continue
            
        name = str(row['Formal_Full_Name']).strip()
        category = str(row['Normalization_Category'])
        
        if not name or name == 'nan':
            continue
            
        print(f"[{index+1}/{total_rows}] Searching: {name} ({category})...")
        
        results = search_wikidata(name)
        
        if results:
            # Heuristic for "Best Match"
            # 1. Exact string match on label
            # 2. First result
            
            best_match = None
            candidates = []
            
            for res in results:
                qid = res.get('id')
                label = res.get('label', '')
                desc = res.get('description', '')
                
                candidate_str = f"{qid} ({label}: {desc})"
                candidates.append(candidate_str)
                
                # Check aliases too
                aliases = res.get('aliases', [])
                # aliases is a list of strings usually? No, in wbsearchentities it might not be returned by default unless requested?
                # Actually wbsearchentities returns 'aliases' as a list of strings if available.
                
                match_found = False
                if label.lower() == name.lower():
                    match_found = True
                else:
                    if aliases:
                        for alias in aliases:
                            if alias.lower() == name.lower():
                                match_found = True
                                break
                
                if match_found:
                    if best_match is None:
                        best_match = res
            
            if best_match:
                df.at[index, 'Wikidata_QID'] = best_match.get('id')
                df.at[index, 'Wikidata_Label'] = best_match.get('label')
                df.at[index, 'Wikidata_Description'] = best_match.get('description')

            df.at[index, 'Wikidata_Candidates'] = " | ".join(candidates)
            
        else:
            df.at[index, 'Wikidata_Candidates'] = "No match found"
            
        # Rate limiting
        time.sleep(0.2)
        
        # Save periodically
        if (index + 1) % 10 == 0:
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            print(f"Saved progress to {output_csv}")

    # Final save
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Completed. Saved to {output_csv}")

if __name__ == "__main__":
    process_audit_list()
