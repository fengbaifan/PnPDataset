import pandas as pd
import requests
import json
import os
import time
from difflib import SequenceMatcher

# Configuration
INPUT_FILE = r"09-QID-Crosscheck/02-Merged_Recheck_With_QID_Cleaned.csv"
OUTPUT_FILE = r"09-QID-Crosscheck/03-Requery_Results.csv"
CACHE_FILE = r"Process-Python/wikidata_search_cache.json"

# Category Rules for filtering/ranking
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
        "limit": 5  # Get top 5 to analyze
    }
    
    try:
        # User-Agent is good practice
        headers = {'User-Agent': 'PnPDatasetBot/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("search", [])
            cache[query] = results
            time.sleep(0.5) # Rate limiting
            return results
    except Exception as e:
        print(f"Error searching '{query}': {e}")
    
    return []

def check_category_match(category, wiki_desc):
    """
    Returns: 'Match', 'Conflict', 'Neutral'
    """
    if pd.isna(category):
        return "Neutral"
    
    # Normalize category
    main_cat = str(category).split('/')[0].strip()
    if main_cat not in CATEGORY_RULES:
        return "Neutral"
    
    rules = CATEGORY_RULES[main_cat]
    desc_lower = str(wiki_desc).lower()
    
    # Check exclusions
    for excl in rules["exclude"]:
        if excl in desc_lower:
            return "Conflict"
            
    # Check keywords
    for kw in rules["keywords"]:
        if kw in desc_lower:
            return "Match"
            
    return "Neutral"

def analyze_results(name, category, results):
    """
    Select the best QID from results based on Name Similarity and Category Match.
    """
    if not results:
        return None, None, None, "No results found"

    best_score = -1
    best_res = None
    reason = ""

    for res in results:
        res_label = res.get('label', '')
        res_desc = res.get('description', '')
        res_id = res.get('id', '')
        
        # 1. Name Similarity (0.0 - 1.0)
        sim = SequenceMatcher(None, name.lower(), res_label.lower()).ratio()
        
        # 2. Category Check
        cat_status = check_category_match(category, res_desc)
        
        # Scoring Logic
        # Base score = similarity * 100
        score = sim * 100
        
        if cat_status == "Match":
            score += 20 # Bonus for correct category
        elif cat_status == "Conflict":
            score -= 50 # Penalty for wrong category
        
        # Exact match bonus
        if name.lower() == res_label.lower():
            score += 10
            
        if score > best_score:
            best_score = score
            best_res = res
            best_cat_status = cat_status
            
    # Final Decision Threshold
    if best_res:
        res_label = best_res.get('label', '')
        res_desc = best_res.get('description', '')
        res_id = best_res.get('id', '')
        
        if best_score >= 90:
            match_type = "High Confidence"
        elif best_score >= 60:
            match_type = "Medium Confidence"
        else:
            match_type = "Low Confidence"
            
        reason = f"Score: {best_score:.1f} (Sim: {SequenceMatcher(None, name.lower(), res_label.lower()).ratio():.2f}, Cat: {best_cat_status})"
        return res_id, res_label, res_desc, f"{match_type} - {reason}"

    return None, None, None, "No suitable match"

def main():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        df = pd.read_csv(INPUT_FILE, encoding='gbk')
        
    cache = load_cache()
    print(f"Loaded cache with {len(cache)} entries.")
    
    print("Starting Wikidata Query...")
    
    # New columns
    df['Query_QID'] = ""
    df['Query_Label'] = ""
    df['Query_Description'] = ""
    df['Query_Logic'] = ""
    
    total = len(df)
    for idx, row in df.iterrows():
        if idx % 10 == 0:
            print(f"Processing {idx}/{total}...", end='\r')
            if idx % 50 == 0:
                save_cache(cache)
                
        name = row['Refined_Formal_Name']
        category = row['Refined_Category']
        
        if pd.isna(name) or str(name).strip() == "":
            df.at[idx, 'Query_Logic'] = "Empty Name"
            continue
            
        results = search_wikidata(name, cache)
        qid, label, desc, logic = analyze_results(name, category, results)
        
        df.at[idx, 'Query_QID'] = qid
        df.at[idx, 'Query_Label'] = label
        df.at[idx, 'Query_Description'] = desc
        df.at[idx, 'Query_Logic'] = logic
        
    save_cache(cache)
    print(f"\nSaving results to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    main()
