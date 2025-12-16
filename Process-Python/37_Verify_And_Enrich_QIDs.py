import pandas as pd
import requests
import time
import os
import json

# Configuration
INPUT_FILE = r"09-QID-Crosscheck/02-Merged_Recheck_With_QID_Cleaned.csv"
OUTPUT_FILE = r"09-QID-Crosscheck/03-Merged_Recheck_QID_Verified.csv"
CACHE_FILE = r"Process-Python/wikidata_cache.json"

# Category Rules (Allowed P31/P279 IDs or Keywords in description)
# This is a simplified rule set for the script
CATEGORY_RULES = {
    "Person": {"keywords": ["human", "person", "painter", "artist", "man", "woman"], "exclude": ["painting", "book", "city", "street"]},
    "Work": {"keywords": ["painting", "drawing", "sculpture", "book", "novel", "film", "work of art", "creative work", "series"], "exclude": ["human", "person", "city"]},
    "Place": {"keywords": ["city", "country", "mountain", "river", "building", "museum", "place", "location", "capital"], "exclude": ["human", "painting"]},
    "Organization": {"keywords": ["museum", "university", "organization", "company", "business", "group"], "exclude": ["human", "painting"]},
    "Event": {"keywords": ["war", "battle", "event", "election"], "exclude": ["human", "city"]},
    "Concept": {"keywords": ["concept", "idea", "genre", "style"], "exclude": ["human"]}
}

# Load Cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        api_cache = json.load(f)
else:
    api_cache = {}

def save_cache():
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(api_cache, f, ensure_ascii=False, indent=2)

def get_wikidata_entities_batch(qids):
    """Fetch details for a list of QIDs (max 50)"""
    ids_str = "|".join(qids)
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": ids_str,
        "format": "json",
        "props": "labels|descriptions|claims|aliases",
        "languages": "en"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("entities", {})
    except Exception as e:
        print(f"Error fetching batch: {e}")
        return {}

def search_wikidata(query):
    """Search for a query string"""
    if query in api_cache:
        return api_cache[query]
        
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json",
        "limit": 5
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("search", [])
        api_cache[query] = results
        return results
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return []

def check_category_match(category, wiki_desc, wiki_claims):
    """
    Check if the local category matches the Wikidata description/claims.
    Returns: 'Match', 'Conflict', 'Unknown'
    """
    if pd.isna(category):
        return "Unknown"
    
    # Normalize category (handle "Person/Group" -> check "Person" rules)
    main_cat = category.split('/')[0].strip()
    if main_cat not in CATEGORY_RULES:
        return "Unknown"
    
    rules = CATEGORY_RULES[main_cat]
    desc_lower = str(wiki_desc).lower()
    
    # Check exclusions first
    for excl in rules["exclude"]:
        if excl in desc_lower:
            return "Conflict"
            
    # Check keywords
    for kw in rules["keywords"]:
        if kw in desc_lower:
            return "Match"
            
    # If no keywords match but no conflict, it's ambiguous/neutral, but we lean towards Unknown or Weak Match
    # For strict verification, we might call it Unknown.
    return "Unknown"

def process_verification(df):
    print("Starting Verification Task...")
    
    # Prepare columns
    df['Verify_Result'] = ""
    df['Verify_Reason'] = ""
    df['Wiki_Label_Found'] = ""
    df['Wiki_Description_Found'] = ""
    
    # Get all QIDs to verify
    qids_to_check = df[df['QID'].notna()]['QID'].unique().tolist()
    qids_to_check = [q for q in qids_to_check if str(q).startswith('Q')]
    
    print(f"Verifying {len(qids_to_check)} unique QIDs...")
    
    # Batch process
    batch_size = 50
    entity_data = {}
    
    for i in range(0, len(qids_to_check), batch_size):
        batch = qids_to_check[i:i+batch_size]
        print(f"Fetching batch {i}/{len(qids_to_check)}...", end='\r')
        results = get_wikidata_entities_batch(batch)
        entity_data.update(results)
        time.sleep(0.5) # Polite delay
        
    print("\nBatch fetch complete. Processing rows...")
    
    for idx, row in df.iterrows():
        qid = row['QID']
        if pd.isna(qid) or not str(qid).startswith('Q'):
            df.at[idx, 'Verify_Result'] = "Skipped"
            continue
            
        entity = entity_data.get(qid)
        if not entity:
            df.at[idx, 'Verify_Result'] = "Invalid"
            df.at[idx, 'Verify_Reason'] = "QID not found in Wikidata"
            continue
            
        # Extract Wiki Info
        labels = entity.get('labels', {})
        wiki_label = labels.get('en', {}).get('value', '')
        descriptions = entity.get('descriptions', {})
        wiki_desc = descriptions.get('en', {}).get('value', '')
        aliases = [a['value'] for a in entity.get('aliases', {}).get('en', [])]
        
        df.at[idx, 'Wiki_Label_Found'] = wiki_label
        df.at[idx, 'Wiki_Description_Found'] = wiki_desc
        
        # 1. Name Check
        local_name = str(row['Refined_Formal_Name']).strip().lower()
        wiki_label_lower = wiki_label.lower()
        aliases_lower = [a.lower() for a in aliases]
        
        name_status = "Mismatch"
        if local_name == wiki_label_lower or local_name in aliases_lower:
            name_status = "Match"
        elif local_name in wiki_label_lower or wiki_label_lower in local_name:
            name_status = "Partial"
            
        # 2. Category Check
        cat_status = check_category_match(row['Refined_Category'], wiki_desc, [])
        
        # 3. Final Verdict
        if name_status == "Match" and cat_status == "Match":
            df.at[idx, 'Verify_Result'] = "Valid"
            df.at[idx, 'Verify_Reason'] = f"Exact name match + Category match ({wiki_desc})"
        elif name_status == "Match" and cat_status == "Conflict":
            df.at[idx, 'Verify_Result'] = "Invalid"
            df.at[idx, 'Verify_Reason'] = f"Name match but Category conflict (Expected {row['Refined_Category']}, got {wiki_desc})"
        elif name_status == "Match":
            df.at[idx, 'Verify_Result'] = "Review"
            df.at[idx, 'Verify_Reason'] = f"Name match but Category unknown/neutral ({wiki_desc})"
        elif name_status == "Partial" and cat_status == "Match":
            df.at[idx, 'Verify_Result'] = "Review"
            df.at[idx, 'Verify_Reason'] = f"Partial name match + Category match"
        elif name_status == "Mismatch":
            df.at[idx, 'Verify_Result'] = "Invalid"
            df.at[idx, 'Verify_Reason'] = f"Name mismatch (Wiki: {wiki_label})"
        else:
            df.at[idx, 'Verify_Result'] = "Review"
            df.at[idx, 'Verify_Reason'] = f"Complex case: Name {name_status}, Cat {cat_status}"

def process_enrichment(df):
    print("Starting Enrichment Task...")
    
    df['Suggested_QID'] = ""
    df['Enrich_Reason'] = ""
    
    # Filter for rows needing enrichment
    mask = df['QID'].isna() | (df['Verify_Result'] == "Invalid")
    indices = df[mask].index
    
    print(f"Enriching {len(indices)} rows...")
    
    count = 0
    for idx in indices:
        count += 1
        if count % 10 == 0:
            print(f"Processed {count}/{len(indices)}...", end='\r')
            save_cache() # Save periodically
            
        name = str(df.at[idx, 'Refined_Formal_Name']).strip()
        category = df.at[idx, 'Refined_Category']
        
        if not name or name == "nan":
            continue
            
        results = search_wikidata(name)
        if not results:
            df.at[idx, 'Enrich_Reason'] = "No search results"
            continue
            
        # Apply Priority Rules
        best_match = None
        candidates = []
        
        for res in results:
            res_label = res.get('label', '')
            res_desc = res.get('description', '')
            res_id = res.get('id', '')
            
            # Check Category
            cat_status = check_category_match(category, res_desc, [])
            
            # Check Name
            name_match = (name.lower() == res_label.lower())
            
            candidates.append(f"{res_id} ({res_label}: {res_desc})")
            
            # Priority 1: Perfect Match
            if name_match and cat_status == "Match":
                best_match = res
                df.at[idx, 'Suggested_QID'] = res_id
                df.at[idx, 'Enrich_Reason'] = f"Perfect Match: {res_label} ({res_desc})"
                break
        
        if not best_match:
            # Priority 2/3: Ambiguous or Partial
            # If we didn't find a perfect match, list top candidates
            df.at[idx, 'Enrich_Reason'] = "Candidates: " + "; ".join(candidates[:3])

    print("\nEnrichment complete.")

def main():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        df = pd.read_csv(INPUT_FILE, encoding='gbk') # Fallback
        
    process_verification(df)
    process_enrichment(df)
    
    print(f"Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    save_cache()
    print("Done.")

if __name__ == "__main__":
    main()
