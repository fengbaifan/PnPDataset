import pandas as pd
import os
import re

# Configuration
input_file = r'c:\Users\001\Desktop\14-Relation\02-worklist\01-Worklist-Plates-Matched-Original.csv'
output_file = r'c:\Users\001\Desktop\14-Relation\02-worklist\04-Worklist-Triples-Refined.csv'

def clean_text(text):
    if pd.isna(text):
        return None
    s = str(text).strip()
    if s.lower() == 'nan' or s == '':
        return None
    return s

def parse_location_string(loc_str):
    """
    Parses a location string which might contain commas.
    Returns a list of triples representing the location chain.
    e.g. "Villa Borghese, Rome" -> [('Villa Borghese', 'located_at', 'Rome')]
    """
    if not loc_str: return []
    
    parts = [p.strip() for p in loc_str.split(',')]
    triples = []
    
    # Chain parts: Part[i] located_at Part[i+1]
    # "Vault, S. Ignazio, Rome" -> Vault -> S. Ignazio -> Rome
    for i in range(len(parts) - 1):
        triples.append({
            'Head': parts[i],
            'Relation': 'located_at',
            'Tail': parts[i+1]
        })
    return triples

def extract_location_suffix(text):
    """
    Extracts location and optional date from suffix like ", Rome" or ", Rome 1642"
    Heuristic: Comma + Space + Capitalized Word (City) + Optional Year
    Returns: (clean_text, location, date)
    """
    if not text: return text, None, None
    
    # Pattern: comma, space, Capitalized Words (City), optional space Year, End of string
    # We exclude common non-location capitalized words if possible, or rely on context.
    # Pattern explanation:
    # , \s+
    # ([A-Z][a-zA-Z\s\.]+)  -> City (starts with Capital, can contain spaces or dots like "S. Ignazio")
    # (?: (\d{4}))?         -> Optional Year
    # $                     -> End
    
    match = re.search(r', ([A-Z][a-zA-Z\.\s]+?)(?: (\d{4}))?$', text)
    if match:
        potential_loc = match.group(1).strip()
        date = match.group(2)
        
        # Filter out common Titles or non-locations
        # This list can be expanded.
        # "Duke of X", "Prince of Y" are titles. "St. X" might be location (Church).
        # "Rome", "Vienna", "London" are fine.
        bad_starts = ['Duke', 'Duchess', 'Prince', 'Princess', 'Earl', 'Count', 'Marquess', 'King', 'Queen', 'Pope', 'Cardinal', 'Portrait', 'View', 'Modello', 'Study']
        
        if any(potential_loc.startswith(x) for x in bad_starts):
            return text, None, None
            
        clean_text = text[:match.start()].strip()
        return clean_text, potential_loc, date
        
    return text, None, None

def decompose_title_info(text):
    """
    Decomposes a title string into components:
    - Author (if "Author: Title")
    - Clean Title (removing Author, Suffixes, "ad Location")
    - Location (from suffix or "ad Location")
    - Date (from suffix)
    
    Returns dict: {'clean_title', 'author', 'location', 'date', 'ad_location'}
    """
    if not text: return {}
    
    info = {'original': text, 'clean_title': text}
    
    # 1. Suffix Location/Date
    clean, loc, date = extract_location_suffix(text)
    if loc: info['location'] = loc
    if date: info['date'] = date
    info['clean_title'] = clean
    
    # 2. Author: Title
    # Only if clean title still looks like Author: Title
    colon_match = re.match(r'^([A-Z][a-zA-Z\s\.]+):\s+(.+)', info['clean_title'])
    if colon_match:
        author = colon_match.group(1).strip()
        work = colon_match.group(2).strip()
        if len(author.split()) <= 4:
             bad_starts = ['Frontispiece', 'Modello', 'Study', 'Plate', 'View', 'Final plate', 'Design', 'Sketch', 'Interior', 'Exterior']
             if not any(author.startswith(x) for x in bad_starts):
                 info['author'] = author
                 info['clean_title'] = work
    
    # 3. "ad Location" (Latin 'at')
    # "Aedes Barberinae ad Quirinalem"
    ad_match = re.search(r'\bad\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?)', info['clean_title'])
    if ad_match:
        info['ad_location'] = ad_match.group(1).strip()
        # Remove "ad X" from clean_title
        info['clean_title'] = info['clean_title'].replace(ad_match.group(0), '').strip()
        # Clean up any trailing/leading punctuation/spaces
        info['clean_title'] = info['clean_title'].strip(', ')

    # DEBUG
    # if 'Girolamo Teti' in text or 'Aedes Barberinae' in text:
    #    print(f"DEBUG: Decompose '{text}' -> {info}")

    return info

def extract_complex_structure(text):
    """
    Analyzes text for complex structures like:
    - "A with view of B"
    - "A with portraits of B and C"
    - "Modello for B"
    - "Final plate of A published by B"
    - "A from the opera B"
    - "Author: Title"
    
    Returns: (Main_Subject, List of (Relation, Target))
    """
    if not text: return None, []
    
    relations = []
    main_subject = text
    
    # 1. "with view of", "with portraits of"
    # Pattern: X with view of Y
    view_match = re.search(r'(.+?),?\s+with\s+(?:view|portraits?)\s+of\s+(.+)', main_subject, re.IGNORECASE)
    if view_match:
        main_subject = view_match.group(1).strip()
        target_str = view_match.group(2).strip()
        
        # Check if multiple targets "Piazzetta and Albrizzi"
        if ' and ' in target_str:
            targets = [t.strip() for t in target_str.split(' and ')]
            for t in targets:
                relations.append(('depicts', t))
        else:
            relations.append(('depicts', target_str))
            
        # Continue processing main_subject

    # 2. "published by" (Handle "Final plate of... published by...")
    pub_match = re.search(r'(.+?),?\s+published by\s+(.+)', main_subject, re.IGNORECASE)
    if pub_match:
        temp_subject = pub_match.group(1).strip()
        publisher_info = pub_match.group(2).strip()
        relations.append(('published_by', publisher_info))
        main_subject = temp_subject

    # 3. "from the opera" / "from opera"
    opera_match = re.search(r'(.+?),?\s+from (?:the )?opera\s+(.+)', main_subject, re.IGNORECASE)
    if opera_match:
        main_subject = opera_match.group(1).strip()
        opera_title = opera_match.group(2).strip()
        relations.append(('part_of', opera_title)) # or derived_from

    # 4. Prefixes: "Modello for", "Study for", "Final plate of", "Frontispiece of"
    prefix_patterns = [
        (r'^(?:Modello|Study|Design|Sketch) for\s+(.+)', 'preparatory_for'),
        (r'^(?:Final plate|Plate) of\s+(.+)', 'part_of'),
        (r'^Frontispiece of\s+(.+)', 'part_of'),
        (r'^(?:Interior|Exterior|View) of\s+(.+)', 'depicts')
    ]
    
    for pat, rel in prefix_patterns:
        match = re.search(pat, main_subject, re.IGNORECASE)
        if match:
            target = match.group(1).strip()
            relations.append((rel, target))
            # We keep main_subject as the full string for Prefixes usually, 
            # as "Modello for X" is the work.
            pass 
            
    # 5. Person Titles: "Paolo Giordano Orsini, Duke of Bracciano"
    # Only if no other complex relations found (to avoid splitting "Modello for X, Rome")
    # AND no commas remaining that were handled by other logic?
    # If we have relations, we skip this heuristic to be safe.
    if ',' in main_subject and not relations:
        parts = [p.strip() for p in main_subject.split(',')]
        if len(parts) == 2:
            # Assume Person, Title
            # But check if 2nd part is Date or Place? (Handled by extract_location_suffix before this function?)
            # If extract_location_suffix is called BEFORE this, then "Rome" is gone.
            # So if we are here, it's likely a Title.
            relations.append(('depicts', parts[0])) # The person
            relations.append(('has_title_role', parts[1])) # The title
            pass

    return main_subject, relations

def extract_provenance(text):
    """
    Extracts provenance/location info from brackets at the end.
    """
    if not text: return text, []
    match = re.search(r'[\(\[]([^\)\]]+)[\)\]]$', text)
    if match:
        content = match.group(1).strip()
        if re.match(r'^\d{4}$', content) or re.match(r'^\d+$', content):
            return text, []
        parts = [p.strip() for p in content.split(',')]
        clean_text = text[:match.start()].strip()
        return clean_text, parts
    return text, []

def extract_embedded_location(text):
    """
    Extracts location introduced by 'at', 'in', 'near'.
    """
    if not text: return text, None, None
    
    # 1. "on vault of", "in church of" patterns (specific to user examples)
    # "fresco on vault of S. Ignazio, Rome"
    # This function is usually called on the Target of a relation, OR the main title.
    
    # Basic " at ", " near " logic
    best_split_idx = -1
    found_prep = None
    # Added " on ", " al " (Italian 'at the')
    for prep in [' at ', ' near ', ' in ', ' on ', ' al ']:
        idx = text.rfind(prep)
        if idx > best_split_idx:
            best_split_idx = idx
            found_prep = prep.strip()
            
    if best_split_idx != -1:
        subject = text[:best_split_idx].strip()
        location = text[best_split_idx + len(found_prep) + 2:].strip() # +2 for spaces
        # Filter dates
        if re.match(r'^\d{4}$', location): return text, None, None
        return subject, location, found_prep
        
    return text, None, None

def process_refined_v2():
    print(f"Reading {input_file}...")
    if not os.path.exists(input_file):
        print("Input file not found.")
        return

    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows.")

    triples = []

    for idx, row in df.iterrows():
        title_raw = clean_text(row.get('Title_Description'))
        work_qid = clean_text(row.get('Title_QID'))
        artist_label = clean_text(row.get('Artist'))
        artist_qid = clean_text(row.get('Artist_QID'))
        location_raw = clean_text(row.get('Location'))
        location_qid = clean_text(row.get('Location_QID'))

        if not title_raw: continue

        # --- Phase 1: Clean Title (Provenance & Embedded Location) ---
        
        # 1. Provenance [Col, City]
        base_title, prov_parts = extract_provenance(title_raw)

        # 2. Extract Complex Structure First (to strip "with view of", "published by", etc. from the Head)
        # We need to do this BEFORE decomposing Author/Suffixes because "with view of" is usually at the end.
        cleaned_base, complex_relations = extract_complex_structure(base_title)
        
        # 3. Decompose Title Info (Author, Title, Suffix Loc/Date, ad Loc)
        # Apply this to the cleaned base title (stripped of clauses)
        main_info = decompose_title_info(cleaned_base)
        
        # Determine the Main Work Node
        # We use the Clean Title as the Head if Author was split, 
        # but if we want to preserve the full string as ID, we might need to be careful.
        # User request implies splitting: "Girolamo Teti: Aedes..." -> "Aedes..."
        # So we use 'clean_title' as the Head.
        work_node = main_info['clean_title']
        
        # Add Decomposed Relations for Main Title
        if 'author' in main_info:
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'created_by', 'Tail': main_info['author'], 'Tail_QID': None, 'Source_Row': idx+2})
        if 'location' in main_info:
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'located_at', 'Tail': main_info['location'], 'Tail_QID': None, 'Source_Row': idx+2})
        if 'date' in main_info:
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'publication_date', 'Tail': main_info['date'], 'Tail_QID': None, 'Source_Row': idx+2})
        if 'ad_location' in main_info:
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'located_at', 'Tail': main_info['ad_location'], 'Tail_QID': None, 'Source_Row': idx+2})

        # 4. Embedded Location (at, near) - Check on the clean title
        # Skip for "Modello for" etc. because the location usually belongs to the target.
        # e.g. "Modello for fresco on vault..." -> "on vault" is for fresco, not Modello.
        skip_embedded = False
        for prefix in ['Modello for', 'Study for', 'Design for', 'Sketch for']:
            if work_node.lower().startswith(prefix.lower()):
                skip_embedded = True
                break
        
        if not skip_embedded:
            subj, loc, prep = extract_embedded_location(work_node)
            if subj and loc:
                work_node = subj # Update Head
                embedded_loc = loc
            else:
                embedded_loc = None
        else:
            embedded_loc = None

        # --- Phase 2: Add Basic Relations ---
        
        # Artist
        if artist_label:
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'created_by', 'Tail': artist_label, 'Tail_QID': artist_qid, 'Source_Row': idx+2})
            
        # Provenance
        if prov_parts:
            owner = prov_parts[0]
            triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'owned_by', 'Tail': owner, 'Tail_QID': None, 'Source_Row': idx+2})
            if len(prov_parts) >= 2:
                city = prov_parts[-1]
                triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'current_location', 'Tail': city, 'Tail_QID': None, 'Source_Row': idx+2})
                if owner != city:
                    triples.append({'Head': owner, 'Head_QID': None, 'Relation': 'located_at', 'Tail': city, 'Tail_QID': None, 'Source_Row': idx+2})

        # Embedded Location
        if embedded_loc:
             triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'located_at', 'Tail': embedded_loc, 'Tail_QID': None, 'Source_Row': idx+2})

        # Explicit Location
        if location_raw:
            loc_chain = parse_location_string(location_raw)
            if loc_chain:
                # Work located at First Element
                triples.append({'Head': work_node, 'Head_QID': work_qid, 'Relation': 'located_at', 'Tail': loc_chain[0]['Head'], 'Tail_QID': location_qid if len(loc_chain)==1 else None, 'Source_Row': idx+2})
                # Chain the rest
                for t in loc_chain:
                    t['Source_Row'] = idx + 2
                    triples.append(t)

        # --- Phase 3: Complex Semantic Analysis ---
        # We already ran extract_complex_structure in Step 2.
        # Now we just need to process the extracted relations.
        
        for rel, target in complex_relations:
            # Recursively decompose the Target
            t_info = decompose_title_info(target)
            t_node = t_info['clean_title']
            
            triples.append({
                'Head': work_node, 'Head_QID': work_qid,
                'Relation': rel,
                'Tail': t_node, 'Tail_QID': None,
                'Source_Row': idx + 2
            })
            
            # Add attributes of the Target
            if 'author' in t_info:
                triples.append({'Head': t_node, 'Head_QID': None, 'Relation': 'created_by', 'Tail': t_info['author'], 'Tail_QID': None, 'Source_Row': idx+2})
            if 'location' in t_info:
                triples.append({'Head': t_node, 'Head_QID': None, 'Relation': 'located_at', 'Tail': t_info['location'], 'Tail_QID': None, 'Source_Row': idx+2})
            if 'date' in t_info:
                triples.append({'Head': t_node, 'Head_QID': None, 'Relation': 'publication_date', 'Tail': t_info['date'], 'Tail_QID': None, 'Source_Row': idx+2})
            if 'ad_location' in t_info:
                triples.append({'Head': t_node, 'Head_QID': None, 'Relation': 'located_at', 'Tail': t_info['ad_location'], 'Tail_QID': None, 'Source_Row': idx+2})
            
            # Check embedded location in Target Clean Title
            t_subj, t_emb_loc, t_prep = extract_embedded_location(t_node)
            if t_emb_loc:
                triples.append({'Head': t_node, 'Head_QID': None, 'Relation': 'located_at', 'Tail': t_emb_loc, 'Tail_QID': None, 'Source_Row': idx+2})

    # Transform to User Schema
    # 序号 | 主体 (Subject) | 主体 QID | 谓语 (Predicate) | 客体 (Object) | 客体 QID | Source_Row
    
    final_rows = []
    
    # Predicate Mapping
    pred_map = {
        'created_by': 'created',
        'located_at': 'is located in',
        'publication_date': 'published in', # Assuming this fits, or keep as is? User only defined created/is located in.
                                            # "Girolamo Teti: Aedes... Rome 1642" -> Published in 1642 makes sense.
        'part_of': 'is part of',            # Normalize to natural language
        'depicts': 'depicts',
        'preparatory_for': 'is preparatory for',
        'owned_by': 'owned by',
        'current_location': 'current location is',
        'published_by': 'published by',
        'has_title_role': 'has title role'
    }
    
    for i, t in enumerate(triples):
        # Map Predicate
        raw_rel = t['Relation']
        new_rel = pred_map.get(raw_rel, raw_rel)
        
        # Handle QIDs
        head_qid = t.get('Head_QID') if t.get('Head_QID') else '/'
        tail_qid = t.get('Tail_QID') if t.get('Tail_QID') else '/'
        
        row = {
            '序号': i + 1,
            '主体 (Subject)': t.get('Head'),
            '主体 QID': head_qid,
            '谓语 (Predicate)': new_rel,
            '客体 (Object)': t.get('Tail'),
            '客体 QID': tail_qid,
            'Source_Row': t.get('Source_Row')
        }
        final_rows.append(row)

    # Save
    triples_df = pd.DataFrame(final_rows)
    # Ensure column order
    cols = ['序号', '主体 (Subject)', '主体 QID', '谓语 (Predicate)', '客体 (Object)', '客体 QID', 'Source_Row']
    
    if not triples_df.empty:
        triples_df = triples_df[cols]
    else:
        triples_df = pd.DataFrame(columns=cols)
        
    print(f"Extracted {len(triples_df)} triples (Refined V2).")
    print(f"Saving to {output_file}...")
    triples_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    process_refined_v2()
