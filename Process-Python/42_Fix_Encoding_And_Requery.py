import pandas as pd
import requests
import json
import os
import time
from difflib import SequenceMatcher

# Configuration
BASE_DIR = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
SOURCE_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "02-Merged_Recheck_With_QID_Cleaned.csv")
TARGET_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "03-Requery_Results.csv")
CACHE_FILE = r"Process-Python/wikidata_search_cache.json"

# Category Rules (Same as before)
CATEGORY_RULES = {
    "Person": {"keywords": ["human", "person", "painter", "artist", "man", "woman", "citizen"], "exclude": ["painting", "book", "city", "street"]},
    "Work": {"keywords": ["painting", "drawing", "sculpture", "book", "novel", "film", "work of art", "creative work", "series", "literary work"], "exclude": ["human", "person", "city"]},
    "Place": {"keywords": ["city", "country", "mountain", "river", "building", "museum", "place", "location", "capital", "architectural structure"], "exclude": ["human", "painting"]},
    "Organization": {"keywords": ["museum", "university", "organization", "company", "business", "group"], "exclude": ["human", "painting"]},
    "Event": {"keywords": ["war", "battle", "event", "election"], "exclude": ["human", "city"]},
    "Concept": {"keywords": ["concept", "idea", "genre", "style"], "exclude": ["human"]}
}

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def search_wikidata(query, cache):
    if not query or pd.isna(query):
        return []
    
    query = str(query).strip()
    if query in cache:
        return cache[query]
        
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json",
        "limit": 5
    }
    
    try:
        headers = {'User-Agent': 'PnPDatasetBot/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("search", [])
            cache[query] = results
            time.sleep(0.5)
            return results
    except Exception as e:
        print(f"Error searching '{query}': {e}")
    
    return []

def check_category_match(category, wiki_desc):
    if pd.isna(category): return "Neutral"
    main_cat = str(category).split('/')[0].strip()
    if main_cat not in CATEGORY_RULES: return "Neutral"
    rules = CATEGORY_RULES[main_cat]
    desc_lower = str(wiki_desc).lower()
    for excl in rules["exclude"]:
        if excl in desc_lower: return "Conflict"
    for kw in rules["keywords"]:
        if kw in desc_lower: return "Match"
    return "Neutral"

def analyze_results(name, category, results):
    if not results:
        return None, None, None, "No results found"

    best_score = -1
    best_res = None
    best_cat_status = "Neutral"

    for res in results:
        res_label = res.get('label', '')
        res_desc = res.get('description', '')
        
        sim = SequenceMatcher(None, name.lower(), res_label.lower()).ratio()
        cat_status = check_category_match(category, res_desc)
        
        score = sim * 100
        if cat_status == "Match": score += 20
        elif cat_status == "Conflict": score -= 50
        if name.lower() == res_label.lower(): score += 10
            
        if score > best_score:
            best_score = score
            best_res = res
            best_cat_status = cat_status
            
    if best_res:
        res_label = best_res.get('label', '')
        res_desc = best_res.get('description', '')
        res_id = best_res.get('id', '')
        
        if best_score >= 90: match_type = "High Confidence"
        elif best_score >= 60: match_type = "Medium Confidence"
        else: match_type = "Low Confidence"
            
        reason = f"Score: {best_score:.1f} (Sim: {SequenceMatcher(None, name.lower(), res_label.lower()).ratio():.2f}, Cat: {best_cat_status})"
        return res_id, res_label, res_desc, f"{match_type} - {reason}"

    return None, None, None, "No suitable match"

def fix_and_requery():
    print("Step 1: Loading clean source data...")
    try:
        df_source = pd.read_csv(SOURCE_FILE, encoding='utf-8-sig')
    except:
        df_source = pd.read_csv(SOURCE_FILE, encoding='utf-8')

    print("Step 2: Loading existing results (potentially corrupted)...")
    try:
        df_target = pd.read_csv(TARGET_FILE, encoding='utf-8-sig')
    except:
        try:
            df_target = pd.read_csv(TARGET_FILE, encoding='gbk')
        except:
            df_target = pd.read_csv(TARGET_FILE, encoding='utf-8')

    # Ensure row counts match
    if len(df_source) != len(df_target):
        print("Error: Row counts mismatch. Aborting.")
        return

    # Step 3: Reconstruct the DataFrame with correct source columns
    df_fixed = df_source.copy()
    df_fixed = df_fixed.rename(columns={
        'QID': 'Original-QID',
        'Refined_Category': 'Original-Refined_Category',
        'Status/Notes': 'Original-Status/Notes'
    })
    
    # Copy existing results
    df_fixed['Second-Query_QID'] = df_target['Second-Query_QID']
    df_fixed['Second-Query_Label'] = df_target['Second-Query_Label']
    df_fixed['Second-Query_Description'] = df_target['Second-Query_Description']
    df_fixed['Second-Query_Logic'] = df_target['Second-Query_Logic']

    # Step 4: Identify rows that need re-querying
    # Criteria: Logic is "No results found" AND Name contains non-ASCII characters (likely encoding issues)
    # Or simply: Logic is "No results found" and the name in Target differed from Source (meaning it was corrupted)
    
    cache = load_cache()
    requery_count = 0
    
    print("Step 4: Checking for rows to re-query...")
    for idx, row in df_fixed.iterrows():
        current_logic = str(row['Second-Query_Logic'])
        name = row['Refined_Formal_Name']
        
        # Check if the name in the target file was corrupted
        target_name = str(df_target.iloc[idx]['Refined_Formal_Name'])
        is_corrupted = target_name != str(name)
        
        # If it was corrupted OR we have no result, let's try again with the correct name
        if is_corrupted or "No results found" in current_logic or pd.isna(row['Second-Query_QID']):
            # Only re-query if we have a valid name
            if pd.notna(name) and str(name).strip() != "":
                # print(f"Re-querying: {name}")
                results = search_wikidata(name, cache)
                qid, label, desc, logic = analyze_results(name, row['Original-Refined_Category'], results)
                
                df_fixed.at[idx, 'Second-Query_QID'] = qid
                df_fixed.at[idx, 'Second-Query_Label'] = label
                df_fixed.at[idx, 'Second-Query_Description'] = desc
                df_fixed.at[idx, 'Second-Query_Logic'] = logic
                requery_count += 1
                
                if requery_count % 10 == 0:
                    print(f"Re-queried {requery_count} rows...", end='\r')

    print(f"\nTotal rows re-queried: {requery_count}")
    save_cache(cache)

    # Step 5: Save back to the original target file location
    print(f"Step 5: Saving fixed dataset to {TARGET_FILE}...")
    df_fixed.to_csv(TARGET_FILE, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    fix_and_requery()
