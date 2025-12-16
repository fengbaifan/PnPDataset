import pandas as pd
import requests
import json
import os
import time
import re
from difflib import SequenceMatcher

# Configuration
BASE_DIR = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
INPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "03-Requery_Results.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "03-Requery_Results_Advanced.csv")
CACHE_FILE = r"Process-Python/wikidata_advanced_cache.json"

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

def analyze_name_structure(name):
    """
    Analyzes the name structure and returns a list of search candidates.
    """
    if pd.isna(name) or str(name).strip() == "":
        return []
    
    name = str(name).strip()
    candidates = [name]
    
    # 1. Remove Parentheses (Context/Artist)
    # "A Dance to the Music of Time (Poussin)" -> "A Dance to the Music of Time"
    if '(' in name:
        no_parens = re.sub(r'\s*\(.*?\)', '', name).strip()
        if no_parens and len(no_parens) > 2:
            candidates.append(no_parens)
            
    # 2. Split by Connectors (Group portraits, Attributions)
    # "A.M. Zanetti the Elder with Marchese Gerini" -> "A.M. Zanetti the Elder"
    connectors = [
        r'\s+with\s+', r'\s+and\s+', r'\s+after\s+', 
        r'\s+attributed to\s+', r'\s+circle of\s+', r'\s+follower of\s+',
        r'\s+studio of\s+', r'\s+school of\s+', r'\s+by\s+'
    ]
    
    for pattern in connectors:
        for cand in list(candidates): # Iterate over copy to allow appending
            parts = re.split(pattern, cand, flags=re.IGNORECASE)
            if len(parts) > 1:
                primary = parts[0].strip()
                if primary and len(primary) > 2:
                    candidates.append(primary)
                    
    # 3. Handle "Portrait of..."
    # "Portrait of X" -> "X" (Finding the person might lead to the work or be a fallback)
    for cand in list(candidates):
        if cand.lower().startswith('portrait of '):
            subject = cand[12:].strip()
            if subject and len(subject) > 2:
                candidates.append(subject)

    # Deduplicate while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique_candidates.append(c)
            
    return unique_candidates

def search_wikidata(query, cache):
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
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("search", [])
            cache[query] = results
            time.sleep(0.2)
            return results
    except Exception as e:
        print(f"Error searching Wikidata '{query}': {e}")
    
    return []

def search_wikipedia(query, cache):
    """
    Search Wikipedia for a page and get its Wikibase Item (QID).
    """
    cache_key = f"WIKI:{query}"
    if cache_key in cache:
        return cache[cache_key]
        
    # 1. Search for the page title
    search_url = "https://en.wikipedia.org/w/api.php"
    search_params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json"
    }
    
    try:
        headers = {'User-Agent': 'PnPDatasetBot/1.0'}
        resp = requests.get(search_url, params=search_params, headers=headers, timeout=5)
        if resp.status_code != 200: return []
        
        data = resp.json()
        if not data or len(data) < 2 or not data[1]:
            cache[cache_key] = []
            return []
            
        page_title = data[1][0]
        
        # 2. Get Page Props (QID) for the title
        prop_params = {
            "action": "query",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "titles": page_title,
            "format": "json"
        }
        
        resp_prop = requests.get(search_url, params=prop_params, headers=headers, timeout=5)
        prop_data = resp_prop.json()
        
        pages = prop_data.get("query", {}).get("pages", {})
        results = []
        
        for page_id, page_info in pages.items():
            if "pageprops" in page_info and "wikibase_item" in page_info["pageprops"]:
                qid = page_info["pageprops"]["wikibase_item"]
                # Construct a result object similar to Wikidata search result
                results.append({
                    "id": qid,
                    "label": page_title,
                    "description": "Wikipedia Page Match",
                    "source": "Wikipedia"
                })
                
        cache[cache_key] = results
        time.sleep(0.2)
        return results
        
    except Exception as e:
        print(f"Error searching Wikipedia '{query}': {e}")
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

def evaluate_match(name, category, result):
    res_label = result.get('label', '')
    res_desc = result.get('description', '')
    
    sim = SequenceMatcher(None, name.lower(), res_label.lower()).ratio()
    cat_status = check_category_match(category, res_desc)
    
    score = sim * 100
    if cat_status == "Match": score += 20
    elif cat_status == "Conflict": score -= 50
    
    # Bonus for Wikipedia source (usually implies notability)
    if result.get('source') == 'Wikipedia':
        score += 5
        
    return score, cat_status

def process_advanced_search():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        df = pd.read_csv(INPUT_FILE, encoding='gbk')
        
    cache = load_cache()
    
    # Filter rows where Second-Query_QID is empty
    # Note: It might be NaN or empty string
    mask = df['Second-Query_QID'].isna() | (df['Second-Query_QID'].astype(str).str.strip() == "")
    target_indices = df[mask].index
    
    print(f"Found {len(target_indices)} rows with missing QIDs to process.")
    
    processed_count = 0
    found_count = 0
    
    for idx in target_indices:
        original_name = df.at[idx, 'Refined_Formal_Name']
        category = df.at[idx, 'Original-Refined_Category']
        
        # 1. Generate Candidates
        candidates = analyze_name_structure(original_name)
        
        best_overall_score = -1
        best_overall_res = None
        best_logic = "No results found (Advanced)"
        
        # 2. Iterate Candidates
        for cand in candidates:
            # Search Wikidata
            wd_results = search_wikidata(cand, cache)
            
            # Search Wikipedia
            wp_results = search_wikipedia(cand, cache)
            
            all_results = wd_results + wp_results
            
            if not all_results:
                continue
                
            # Evaluate results for this candidate
            for res in all_results:
                score, cat_status = evaluate_match(cand, category, res)
                
                # If we are matching a simplified name (e.g. "Poussin" from "Title (Poussin)"), 
                # we must be careful. The category must match strictly.
                # If original name was "Title (Artist)" and we search "Title", score is high.
                # If we search "Artist", score is low against original name, but high against candidate.
                # We should compare score against the CANDIDATE name for similarity, 
                # but maybe penalize if candidate is much shorter than original?
                
                # Let's stick to simple logic: If we find a High Confidence match for a candidate, we take it.
                
                if score > best_overall_score:
                    best_overall_score = score
                    best_overall_res = res
                    best_logic = f"Advanced Match via '{cand}': Score {score:.1f} ({cat_status})"
        
        # 3. Update if we found something decent
        if best_overall_res and best_overall_score > 60: # Threshold
            df.at[idx, 'Second-Query_QID'] = best_overall_res.get('id')
            df.at[idx, 'Second-Query_Label'] = best_overall_res.get('label')
            df.at[idx, 'Second-Query_Description'] = best_overall_res.get('description')
            df.at[idx, 'Second-Query_Logic'] = best_logic
            found_count += 1
            
        processed_count += 1
        if processed_count % 10 == 0:
            print(f"Processed {processed_count}/{len(target_indices)} | Found: {found_count}...", end='\r')
            if processed_count % 50 == 0:
                save_cache(cache)
                
    print(f"\nProcessing complete. Found {found_count} new matches.")
    save_cache(cache)
    
    print(f"Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    process_advanced_search()
