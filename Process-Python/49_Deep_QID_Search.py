import pandas as pd
import requests
import json
import os
import time
import re
from difflib import SequenceMatcher

# Configuration
BASE_DIR = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
INPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "05-Missing_QID_Report_Filled.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "06-Deep_Query_Results.csv")
CACHE_FILE = r"Process-Python/wikidata_deep_cache.json"

# Context Mapping (Chinese -> English Keywords)
NOTE_KEYWORDS = {
    "画": ["painting", "drawing", "art"],
    "肖像": ["portrait"],
    "雕塑": ["sculpture", "statue"],
    "教堂": ["church", "basilica", "cathedral"],
    "宫殿": ["palace"],
    "家族": ["family", "house of"],
    "广场": ["square", "piazza"],
    "剧院": ["theatre", "opera house"],
    "博物馆": ["museum", "gallery"],
    "大学": ["university", "college"],
    "别墅": ["villa"],
    "花园": ["garden", "park"],
    "人": ["person", "human"],
    "画家": ["painter", "artist"],
    "作家": ["writer", "author"],
    "皇帝": ["emperor"],
    "教皇": ["pope"],
    "神话": ["mythology", "god", "goddess"],
    "别名": ["alias", "known as"],
    "又名": ["alias", "known as"],
    "指": ["refers to"],
    "即": ["is", "same as"]
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

def clean_name(name):
    # Remove text in parentheses
    name = re.sub(r'\s*\(.*?\)', '', name)
    # Remove text in brackets
    name = re.sub(r'\s*\[.*?\]', '', name)
    return name.strip()

def extract_entities_from_notes(notes):
    """
    Extract potential English names or specific entities mentioned in Chinese notes.
    e.g. "即 Giovanni Battista" -> "Giovanni Battista"
    """
    if pd.isna(notes):
        return []
    
    extracted = []
    # Look for English words in the notes
    english_parts = re.findall(r'[A-Za-z][A-Za-z\s\.\-\']{2,}', str(notes))
    for part in english_parts:
        part = part.strip()
        if len(part) > 3 and part.lower() not in ["validation", "disambiguation", "category fix", "ocr fix"]:
            extracted.append(part)
            
    return extracted

def generate_deep_queries(row):
    name = str(row['Refined_Formal_Name']).strip()
    notes = str(row['Original-Status/Notes'])
    category = str(row['Original-Refined_Category'])
    
    queries = []
    
    # 1. Base Name Cleaning
    clean = clean_name(name)
    if clean and clean != name:
        queries.append({"q": clean, "type": "Cleaned Name", "boost": 1.0})
        
    # 2. Split by Connectors (Segmentation)
    connectors = [
        r'\s+with\s+', r'\s+and\s+', r'\s+after\s+', 
        r'\s+attributed to\s+', r'\s+circle of\s+', r'\s+follower of\s+',
        r'\s+studio of\s+', r'\s+school of\s+', r'\s+by\s+', r'\s+formerly\s+'
    ]
    
    for pattern in connectors:
        parts = re.split(pattern, name, flags=re.IGNORECASE)
        if len(parts) > 1:
            for part in parts:
                p = part.strip()
                if len(p) > 3:
                    queries.append({"q": p, "type": "Segment", "boost": 0.8})
                    
    # 3. "Portrait of..." specific handling
    if "portrait of" in name.lower():
        subject = re.sub(r'portrait of\s+', '', name, flags=re.IGNORECASE).strip()
        if subject:
            queries.append({"q": subject, "type": "Subject", "boost": 0.9})
            
    # 4. Context Injection from Notes
    context_keywords = []
    for cn_key, en_vals in NOTE_KEYWORDS.items():
        if cn_key in notes:
            context_keywords.extend(en_vals)
            
    # Add queries combining Name + Context
    # Only do this if we haven't found many queries or for the clean name
    targets = [name]
    if clean: targets.append(clean)
    
    for t in set(targets):
        for ctx in context_keywords[:3]: # Limit to top 3 context words to avoid explosion
            queries.append({"q": f"{t} {ctx}", "type": "Contextual", "boost": 0.85})
            
    # 5. Extract English names from Notes (often the correct entity name is hidden there)
    note_entities = extract_entities_from_notes(notes)
    for ne in note_entities:
        queries.append({"q": ne, "type": "From Notes", "boost": 0.95})
        
    # Deduplicate queries
    seen = set()
    unique_queries = []
    for q_obj in queries:
        q_str = q_obj['q'].lower()
        if q_str not in seen and len(q_str) > 2:
            seen.add(q_str)
            unique_queries.append(q_obj)
            
    return unique_queries

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
        print(f"Error searching '{query}': {e}")
    
    return []

def evaluate_result(original_name, query_info, result):
    res_label = result.get('label', '')
    res_desc = result.get('description', '')
    
    # Similarity between the SEARCH QUERY and the RESULT LABEL
    # We use the query text because sometimes we search for a segment (e.g. "Poussin") 
    # and we want to match "Nicolas Poussin".
    query_text = query_info['q']
    sim = SequenceMatcher(None, query_text.lower(), res_label.lower()).ratio()
    
    score = sim * 100
    
    # Apply Boost
    score *= query_info['boost']
    
    # Context Check (Bonus)
    # If the description contains words from our context list, boost it
    # (Simplified check)
    if "painting" in res_desc.lower() or "portrait" in res_desc.lower():
        if "Work" in str(query_info.get('category', '')):
            score += 10
            
    return score

def process_deep_search():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        df = pd.read_csv(INPUT_FILE, encoding='gbk')
        
    cache = load_cache()
    
    # Initialize new columns
    df['Third-Query_QID'] = ""
    df['Third-Query_Label'] = ""
    df['Third-Query_Description'] = ""
    df['Third-Query_Logic'] = ""
    
    # Filter for rows where Second-Query_QID is still missing
    mask = df['Second-Query_QID'].isna() | (df['Second-Query_QID'].astype(str).str.strip() == "")
    target_indices = df[mask].index
    
    print(f"Processing {len(target_indices)} rows for Deep Search...")
    
    found_count = 0
    processed_count = 0
    
    for idx in target_indices:
        row = df.iloc[idx]
        queries = generate_deep_queries(row)
        
        best_res = None
        best_score = 0
        best_logic = ""
        
        for q_obj in queries:
            # Pass category for context checking
            q_obj['category'] = row['Original-Refined_Category']
            
            results = search_wikidata(q_obj['q'], cache)
            
            for res in results:
                score = evaluate_result(row['Refined_Formal_Name'], q_obj, res)
                
                if score > best_score:
                    best_score = score
                    best_res = res
                    best_logic = f"Deep Match via '{q_obj['q']}' ({q_obj['type']}): {res.get('label')} (Score: {score:.1f})"
        
        # Threshold
        if best_res and best_score > 65:
            df.at[idx, 'Third-Query_QID'] = best_res.get('id')
            df.at[idx, 'Third-Query_Label'] = best_res.get('label')
            df.at[idx, 'Third-Query_Description'] = best_res.get('description')
            df.at[idx, 'Third-Query_Logic'] = best_logic
            found_count += 1
            
        processed_count += 1
        if processed_count % 10 == 0:
            print(f"Processed {processed_count}/{len(target_indices)} | Found: {found_count}...", end='\r')
            if processed_count % 50 == 0:
                save_cache(cache)
                
    print(f"\nDeep search complete. Found {found_count} new matches.")
    save_cache(cache)
    
    print(f"Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    process_deep_search()
