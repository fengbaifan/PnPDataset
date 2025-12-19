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
OUTPUT_FILE = os.path.join(BASE_DIR, "09-QID-Crosscheck", "06-Deep_Analysis_Results.csv")
CACHE_FILE = r"Process-Python/wikidata_deep_cache.json"

# Headers for requests
HEADERS = {
    'User-Agent': 'PnPDatasetBot/1.0 (mailto:your_email@example.com)',
    'Accept-Encoding': 'gzip, deflate'
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

CACHE = load_cache()

def search_wikidata(query, language='en'):
    """
    Search Wikidata for a query string.
    """
    cache_key = f"wd_{query}_{language}"
    if cache_key in CACHE:
        return CACHE[cache_key]

    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": language,
        "limit": 5,
        "format": "json"
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("search", [])
            CACHE[cache_key] = results
            return results
    except Exception as e:
        print(f"Error searching Wikidata for {query}: {e}")
        time.sleep(1)
    
    return []

def extract_potential_names_from_notes(notes):
    """
    Extract potential English names or specific Chinese names from notes.
    """
    if pd.isna(notes):
        return []
    
    candidates = []
    
    # Pattern 1: "可能是 X" or "指 X" (Possibly X / Refers to X)
    # Capture English names inside Chinese text
    english_names = re.findall(r'[A-Za-z\s\.\-\']{3,}', str(notes))
    for name in english_names:
        clean_name = name.strip()
        if len(clean_name) > 3 and clean_name.lower() not in ['category fix', 'validation', 'ocr fix', 'context']:
            candidates.append(clean_name)
            
    return candidates

def split_entity_name(name):
    """
    Split entity name into components for separate searching.
    """
    # 1. Split by " / " (Alternative names)
    if " / " in name:
        return [p.strip() for p in name.split(" / ")]
    
    # 2. Split by " with " (Two people)
    if " with " in name:
        return [p.strip() for p in name.split(" with ")]
        
    # 3. Split by " and " (Two entities)
    if " and " in name:
        return [p.strip() for p in name.split(" and ")]
        
    # 4. Split "X (Y)" -> Search X, Search Y
    match = re.match(r"^(.*?)\s*\((.*?)\)$", name)
    if match:
        return [match.group(1).strip(), match.group(2).strip()]
        
    # 5. Remove "The " prefix
    if name.lower().startswith("the "):
        return [name[4:]]
        
    return []

def clean_query(query):
    """
    Remove common stopwords for better search.
    """
    stopwords = [
        "A Scene from", "Allegory of", "Altar of", "Portrait of", "View of", 
        "Design for", "Sketch for", "Study for", "The ", "An "
    ]
    
    cleaned = query
    for sw in stopwords:
        if cleaned.lower().startswith(sw.lower()):
            cleaned = cleaned[len(sw):].strip()
            
    return cleaned

def analyze_row(row):
    """
    Perform deep analysis on a single row.
    """
    # If already found, skip
    if pd.notna(row['Second-Query_QID']) and str(row['Second-Query_QID']).startswith('Q'):
        return row['Second-Query_QID'], row['Second-Query_Label'], row['Second-Query_Description'], "Existing"

    original_name = str(row['Refined_Formal_Name']).strip()
    notes = row['Original-Status/Notes']
    category = row['Original-Refined_Category']
    
    candidates = []
    
    # Strategy 1: Clean Name (Remove "Allegory of", etc.)
    cleaned_name = clean_query(original_name)
    if cleaned_name != original_name:
        candidates.append((cleaned_name, "Cleaned Name"))
        
    # Strategy 2: Split Name
    splits = split_entity_name(original_name)
    for s in splits:
        candidates.append((s, "Split Part"))
        
    # Strategy 3: Extract from Notes
    note_names = extract_potential_names_from_notes(notes)
    for n in note_names:
        candidates.append((n, "From Notes"))
        
    # Strategy 4: Original Name (if not tried successfully before, but we assume it was)
    # We add it again just in case the previous search was strict
    candidates.append((original_name, "Original"))

    # Execute Searches
    best_match = None
    best_score = 0
    
    print(f"Analyzing: {original_name}")
    
    for query, method in candidates:
        if len(query) < 3: continue
        
        print(f"  -> Searching: {query} ({method})")
        results = search_wikidata(query)
        
        for res in results:
            qid = res.get('id')
            label = res.get('label', '')
            desc = res.get('description', '')
            
            # Scoring Logic
            score = 0
            
            # 1. Name Similarity
            sim = SequenceMatcher(None, query.lower(), label.lower()).ratio()
            score += sim * 50
            
            # 2. Category Match (Simple heuristic)
            if category == 'Person' and ('human' in desc.lower() or 'painter' in desc.lower() or 'born' in desc.lower()):
                score += 30
            elif category == 'Work' and ('painting' in desc.lower() or 'work' in desc.lower() or 'book' in desc.lower()):
                score += 30
            elif category == 'Place' and ('church' in desc.lower() or 'palace' in desc.lower() or 'city' in desc.lower()):
                score += 30
                
            # 3. Context Match from Notes
            if pd.notna(notes):
                # Check if description matches keywords in notes (translated)
                # This is hard to do perfectly, but we can check for overlap
                pass

            if score > best_score:
                best_score = score
                best_match = {
                    'qid': qid,
                    'label': label,
                    'desc': desc,
                    'logic': f"{method} (Score: {int(score)})"
                }
    
    if best_match and best_score > 60: # Threshold
        return best_match['qid'], best_match['label'], best_match['desc'], best_match['logic']
    
    return None, None, None, "No results found"

def main():
    df = pd.read_csv(INPUT_FILE)
    
    # Add new columns for Deep Analysis if they don't exist
    if 'Deep_Analysis_QID' not in df.columns:
        df['Deep_Analysis_QID'] = None
        df['Deep_Analysis_Label'] = None
        df['Deep_Analysis_Description'] = None
        df['Deep_Analysis_Logic'] = None
        
    total = len(df)
    processed = 0
    found_count = 0
    
    for index, row in df.iterrows():
        # Only process if Second-Query_QID is missing
        if pd.isna(row['Second-Query_QID']):
            qid, label, desc, logic = analyze_row(row)
            
            if qid:
                df.at[index, 'Deep_Analysis_QID'] = qid
                df.at[index, 'Deep_Analysis_Label'] = label
                df.at[index, 'Deep_Analysis_Description'] = desc
                df.at[index, 'Deep_Analysis_Logic'] = logic
                found_count += 1
                print(f"    FOUND: {qid} - {label}")
        
        processed += 1
        if processed % 10 == 0:
            save_cache(CACHE)
            
    save_cache(CACHE)
    
    # Save results
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Deep analysis complete. Found {found_count} new matches.")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
