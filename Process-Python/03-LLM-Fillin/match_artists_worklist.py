import csv
import os
import re

def normalize(text):
    return str(text).strip()

def match_artist(query, candidates):
    if not query:
        return None, None
    
    query_norm = normalize(query).lower()
    
    # 1. Exact Match
    for name, qid in candidates.items():
        if normalize(name).lower() == query_norm:
            return name, qid
            
    # 2. Token match (Query is a word in Name)
    matches = []
    for name, qid in candidates.items():
        name_norm = normalize(name).lower()
        # Check if query is a distinct word in name
        # e.g. "Bernini" in "Gian Lorenzo Bernini"
        try:
            if re.search(r'\b' + re.escape(query_norm) + r'\b', name_norm):
                matches.append((name, qid))
        except:
            # Fallback for special chars
            if query_norm in name_norm:
                matches.append((name, qid))
    
    # 3. Surname Match (Fallback)
    if not matches:
        # Get last word of query
        # Remove trailing punctuation
        clean_query = re.sub(r'[^\w\s]', '', query_norm)
        words = clean_query.split()
        if len(words) > 0:
            last_name = words[-1]
            # Avoid matching common short words or if query is just one word (already covered by token match)
            # If query is "Guido Abbatini", last name is "abbatini".
            if len(last_name) > 3: 
                for name, qid in candidates.items():
                    name_norm = normalize(name).lower()
                    clean_name = re.sub(r'[^\w\s]', '', name_norm)
                    name_words = clean_name.split()
                    if name_words and name_words[-1] == last_name:
                         matches.append((name, qid))

    if matches:
        # Sort matches to have deterministic output
        matches.sort(key=lambda x: x[0])
        
        # If too many matches (e.g. > 5), it might be too generic. Limit it?
        # But for "Bernini", we expect 3.
        
        unique_names = []
        unique_qids = []
        seen_names = set()
        
        for m_name, m_qid in matches:
            if m_name not in seen_names:
                unique_names.append(m_name)
                seen_names.add(m_name)
            if m_qid and m_qid not in unique_qids:
                unique_qids.append(m_qid)
        
        return "; ".join(unique_names), "; ".join(unique_qids)
        
    return None, None

def process():
    combined_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\09-MissingQID-LLM-Fillin\04-QID-Combine ORGfile\07-Requery_Filled_Combined.csv"
    # Adjusted path based on Glob finding
    worklist_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\10-Worklist-index\Worklist_Plates.csv"
    output_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\10-Worklist-index\worklist-02.csv"
    
    if not os.path.exists(worklist_path):
        print(f"Error: Worklist file not found at {worklist_path}")
        return

    # Load 07 data
    candidates = {} # Name -> QID 
    
    with open(combined_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Refined_Formal_Name')
            qid = row.get('Original-QID') or row.get('Second-Query_QID') or row.get('LLM-Fillin_QID')
            if name:
                candidates[name] = qid
                
    print(f"Loaded {len(candidates)} candidates from combined dataset.")

    # Load Worklist
    with open(worklist_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames + ['Matched_Full_Name', 'Matched_QID']
        
    # Process
    matched_count = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            artist = row.get('Artist')
            matched_name, matched_qid = match_artist(artist, candidates)
            
            if matched_name:
                matched_count += 1
            
            row['Matched_Full_Name'] = matched_name if matched_name else ""
            row['Matched_QID'] = matched_qid if matched_qid else ""
            
            writer.writerow(row)
            
    print(f"Processing complete.")
    print(f"Matched {matched_count} out of {len(rows)} rows.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    process()
