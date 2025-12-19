import pandas as pd
import requests
import json
import os
import time
import re
from difflib import SequenceMatcher

# Configuration
BASE_DIR = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
INPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "05-Missing_QID_Report.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "05-Missing_QID_Report_Filled.csv")
CACHE_FILE = r"Process-Python/wikipedia_smart_cache.json"

# Context Mapping (Chinese -> English Suffix)
CONTEXT_MAP = {
    "画": "painting",
    "图": "painting",
    "像": "portrait",
    "书": "book",
    "小说": "novel",
    "雕塑": "sculpture",
    "教堂": "church",
    "宫": "palace",
    "家族": "family",
    "广场": "square",
    "运河": "canal",
    "剧院": "theatre",
    "博物馆": "museum",
    "大学": "university",
    "桥": "bridge",
    "别墅": "villa",
    "花园": "garden",
    "公园": "park",
    "街": "street",
    "路": "road",
    "人": "person",
    "画家": "painter",
    "作家": "writer",
    "皇帝": "emperor",
    "教皇": "pope",
    "神": "god",
    "神话": "mythology"
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

def get_context_from_notes(notes):
    if pd.isna(notes):
        return []
    
    notes = str(notes)
    contexts = set()
    
    for key, value in CONTEXT_MAP.items():
        if key in notes:
            contexts.add(value)
            
    return list(contexts)

def search_wikipedia_smart(query, cache):
    """
    Search Wikipedia using the query. Returns list of {id, label, description}.
    """
    if query in cache:
        return cache[query]
        
    url = "https://en.wikipedia.org/w/api.php"
    
    # 1. Try Opensearch first (good for exact titles)
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 3,
        "namespace": 0,
        "format": "json"
    }
    
    results = []
    try:
        headers = {'User-Agent': 'PnPDatasetBot/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 1:
                titles = data[1]
                for title in titles:
                    # Get QID for this title
                    qid = get_qid_from_title(title, headers)
                    if qid:
                        results.append({
                            "id": qid,
                            "label": title,
                            "description": "Wikipedia Match",
                            "source": "Wikipedia"
                        })
    except Exception as e:
        print(f"Error in opensearch '{query}': {e}")

    # 2. If no results, try 'query' action with srsearch (full text search)
    if not results:
        params_sr = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 3,
            "format": "json"
        }
        try:
            resp = requests.get(url, params=params_sr, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                search_items = data.get("query", {}).get("search", [])
                for item in search_items:
                    title = item["title"]
                    qid = get_qid_from_title(title, headers)
                    if qid:
                        results.append({
                            "id": qid,
                            "label": title,
                            "description": "Wikipedia Search Result",
                            "source": "Wikipedia"
                        })
        except Exception as e:
            print(f"Error in srsearch '{query}': {e}")

    cache[query] = results
    time.sleep(0.5)
    return results

def get_qid_from_title(title, headers):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "titles": title,
        "format": "json"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                return page["pageprops"]["wikibase_item"]
    except:
        pass
    return None

def process_smart_search():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        df = pd.read_csv(INPUT_FILE, encoding='gbk')
        
    cache = load_cache()
    
    print(f"Processing {len(df)} rows...")
    
    found_count = 0
    
    for idx, row in df.iterrows():
        # Skip if already filled (though input file should be all missing)
        if pd.notna(row['Second-Query_QID']) and str(row['Second-Query_QID']).strip() != "":
            continue
            
        name = str(row['Refined_Formal_Name']).strip()
        notes = row['Original-Status/Notes']
        category = row['Original-Refined_Category']
        
        # 1. Determine Contexts
        contexts = get_context_from_notes(notes)
        
        # 2. Generate Queries
        queries = []
        
        # Base query
        queries.append(name)
        
        # Context queries
        for ctx in contexts:
            queries.append(f"{name} {ctx}")
            queries.append(f"{name} ({ctx})")
            
        # Category specific queries (if not covered by notes)
        if "Work" in str(category) and "painting" not in contexts:
            queries.append(f"{name} painting")
        if "Place" in str(category) and "building" not in contexts:
            queries.append(f"{name} building")
            
        # 3. Execute Search
        best_res = None
        best_score = 0
        best_logic = ""
        
        for q in queries:
            results = search_wikipedia_smart(q, cache)
            
            for res in results:
                # Simple scoring: Similarity of label to original name
                # But if we searched with context, the label might be "Name (painting)"
                # So we check if the original name is a substring or high similarity
                
                res_label = res['label']
                
                # Clean label for comparison (remove parenthesis)
                label_clean = re.sub(r'\s*\(.*?\)', '', res_label)
                
                sim = SequenceMatcher(None, name.lower(), label_clean.lower()).ratio()
                
                score = sim * 100
                
                # Bonus if context matches
                if any(ctx in res_label.lower() for ctx in contexts):
                    score += 10
                    
                if score > best_score:
                    best_score = score
                    best_res = res
                    best_logic = f"Smart Match via '{q}': {res_label} ({score:.1f})"
        
        # 4. Update if good match
        if best_res and best_score > 70: # Slightly higher threshold
            df.at[idx, 'Second-Query_QID'] = best_res['id']
            df.at[idx, 'Second-Query_Label'] = best_res['label']
            df.at[idx, 'Second-Query_Description'] = best_res['description']
            df.at[idx, 'Second-Query_Logic'] = best_logic
            found_count += 1
            print(f"Found: {name} -> {best_res['label']} ({best_res['id']})")
            
        if idx % 10 == 0:
            save_cache(cache)
            
    print(f"\nSmart search complete. Found {found_count} new matches.")
    save_cache(cache)
    
    print(f"Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    process_smart_search()
