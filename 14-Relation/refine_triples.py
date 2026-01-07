import pandas as pd
import re
import os
import glob

input_dir = r'c:\Users\001\Desktop\14-Relation\06-Extraction-Rules'

# Descriptive prefixes that indicate a list of items
LIST_PREFIXES = [
    'portraits of', 'busts of', 'statues of', 'views of', 'drawings of', 
    'etchings of', 'sketches of', 'designs for', 'projects for', 'plans for',
    'visits to', 'journeys to', 'travels to', 'trips to',
    'membership of', 'editions of', 'works of', 'copies of', 'engravings of',
    'purchase of', 'sale of', 'collection of', 'acquisition of', 'payment for',
    'friendship with', 'correspondence with', 'relations with', 'dispute with',
    'patronage of', 'support of', 'protection of',
    'frescoes of', 'paintings of', 'sculptures of', 'decorations of', 'illustrations for',
    'scenes from', 'stories from',
    'double portrait of', 'self-portrait with'
]

# Prefixes where it is safe to split by comma (unlikely to contain comma in entity name)
COMMA_SAFE_PREFIXES = [
    'editions of', 'works of', 'membership of', 'portraits of', 'busts of', 
    'statues of', 'drawings of', 'etchings of', 'sketches of', 'copies of', 
    'engravings of', 'designs for', 'projects for', 'plans for',
    'purchase of', 'sale of', 'collection of', 'acquisition of',
    'frescoes of', 'paintings of', 'sculptures of', 'decorations of',
    'friendship with', 'correspondence with', 'patronage of', 'support of',
    'double portrait of', 'self-portrait with'
]

def clean_object(text):
    return text.strip().strip('.,;')

def split_subject_names(subject):
    """
    Splits subjects like "Surname, Name1 and Name2" into two subjects.
    Also handles "Name1 and Name2 Surname" (less common).
    """
    # Pattern 1: Surname, Name1 and Name2 (e.g., "Valeriani, Domenico and Giuseppe")
    match1 = re.match(r'^([A-Z][a-z]+),\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)$', subject)
    if match1:
        surname = match1.group(1)
        name1 = match1.group(2)
        name2 = match1.group(3)
        return [f"{surname}, {name1}", f"{surname}, {name2}"]
    
    # Pattern 3: Simple "Name1 and Name2" (e.g. "Guercino and Preti")
    match3 = re.match(r'^([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)$', subject)
    if match3:
        return [match3.group(1), match3.group(2)]

    return [subject]

def split_list(text, prefix):
    # Remove prefix
    content = text[len(prefix):].strip()
    
    # Determine splitting strategy
    # "visits to" might have "City, Country" so we avoid splitting by comma for those unless sure
    is_comma_safe = any(prefix.lower().startswith(p) for p in COMMA_SAFE_PREFIXES)
    
    if is_comma_safe:
        # Split by ", and ", " and ", ", "
        parts = re.split(r',?\s+and\s+|,\s+', content)
    else:
        # Only split by " and "
        parts = re.split(r'\s+and\s+', content)
    
    results = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
            
        # Handle repeated "of" or "to"
        # If prefix ends with " of" and p starts with "of ", remove "of " from p
        if prefix.lower().endswith(' of') and p.lower().startswith('of '):
            p = p[3:].strip()
        elif prefix.lower().endswith(' to') and p.lower().startswith('to '):
             p = p[3:].strip()
             
        results.append(f"{prefix} {p}")
    return results

def split_noun_prep_list(text):
    """
    Splits "Head + Prep + List" into multiple items.
    e.g. "attempts to obtain public commissions for Guercino and Preti"
    -> "attempts to obtain public commissions for Guercino", "... for Preti"
    """
    # Order matters: specific/longer preps first? Or just common ones.
    # "by" is good to handle "prints for by X and Y".
    preps = ['by', 'with', 'for', 'from', 'of', 'in']
    
    for prep in preps:
        # Regex: ^(.+)\s+prep\s+(.+)$
        # We use strict spaces around prep.
        pattern = re.compile(r'^(.*)\s+' + prep + r'\s+(.+)$', re.IGNORECASE)
        match = pattern.match(text)
        if match:
            head = match.group(1)
            tail = match.group(2)
            
            # Check if tail contains a list indicator
            if ' and ' in tail:
                # Heuristic: if comma is present, use comma splitting
                if ',' in tail:
                    parts = re.split(r',?\s+and\s+|,\s+', tail)
                else:
                    parts = tail.split(' and ')
                
                parts = [p.strip() for p in parts if p.strip()]
                
                if len(parts) > 1:
                    results = []
                    for p in parts:
                        results.append(f"{head} {prep} {p}")
                    return results
                    
    return [text]

def split_pure_list(text):
    """
    Splits a pure list of entities like "A, B and C".
    Only applies if the text seems to be just a list (no complex structure).
    """
    if ' and ' not in text:
        return [text]
        
    # Heuristic: Must contain comma (for "A, B and C") or just "A and B".
    # But "A and B" is handled by simple regexes usually.
    # This function targets "A, B, C and D".
    
    if ',' not in text:
        return [text]
    
    # Avoid splitting sentences.
    # Avoid splitting "Name, Title" (e.g. "Zanetti, A. M., the Elder").
    # If "Zanetti, A. M., the Elder" -> 3 commas. But no "and".
    
    # If text has " and " and commas.
    parts = re.split(r',?\s+and\s+|,\s+', text)
    parts = [p.strip() for p in parts if p.strip()]
    
    # Check if parts look valid.
    # If any part is very long (>50 chars) or contains verbs?
    # Let's trust the split for now if it generates > 1 parts.
    if len(parts) > 1:
        return parts
        
    return [text]

def split_compound_noun_prep(text):
    # Rule 10 logic: Noun(s) and Noun(s) Prep Entity
    # Regex: ^([a-z]+(?: [a-z]+)*s)\s+and\s+([a-z]+(?: [a-z]+)*s)\s+(for|from|in|with|by)\s+(.+)$
    match_noun_prep = re.match(r'^([a-z]+(?: [a-z]+)*s)\s+and\s+([a-z]+(?: [a-z]+)*s)\s+(for|from|in|with|by)\s+(.+)$', text)
    if match_noun_prep:
        noun1 = match_noun_prep.group(1)
        noun2 = match_noun_prep.group(2)
        prep = match_noun_prep.group(3)
        tail = match_noun_prep.group(4)
        return [f"{noun1} {prep} {tail}", f"{noun2} {prep} {tail}"]
    return [text]

def refine_row(row):
    """
    Returns a list of rows (dicts).
    """
    subject = row['Subject']
    predicate = row['Predicate']
    obj = str(row['Object'])
    source_raw = row['Source_Raw']
    
    new_rows = []
    
    # --- SUBJECT SPLITTING ---
    split_subjects = split_subject_names(subject)
    
    if len(split_subjects) == 1:
        # Check prefix list
        lower_subj = subject.lower()
        for prefix in LIST_PREFIXES:
            if lower_subj.startswith(prefix + ' ') and ' and ' in lower_subj:
                actual_prefix = subject[:len(prefix)]
                split_subjects = split_list(subject, actual_prefix)
                break
    
    if len(split_subjects) == 1:
        split_subjects = split_compound_noun_prep(subject)
        
    if len(split_subjects) == 1:
        split_subjects = split_noun_prep_list(subject)

    if len(split_subjects) == 1:
        # Only apply pure list if it looks like a list of names/entities
        # and not a sentence.
        # Simple heuristic: capitalized words?
        split_subjects = split_pure_list(subject)

    # --- ROW GENERATION ---
    final_rows = []
    
    for sub in split_subjects:
        # Special check for 'intended_for':
        # If we split the subject, we must ensure the 'Object' is relevant to the 'sub'.
        # e.g. Subject="attempts for G and P", Object="G".
        # Split S -> "attempts for G", "attempts for P".
        # "attempts for P" --intended_for--> "G" is WRONG.
        if predicate == 'intended_for':
            # Heuristic: Object name must be in Subject string?
            # Or some overlap.
            if obj in sub:
                 pass # Keep it
            else:
                 # If Object is NOT in sub, likely this split subject doesn't belong to this relation.
                 # BUT: "attempts for Guercino" contains "Guercino".
                 # "attempts for Preti" does NOT contain "Guercino".
                 # So we SKIP "attempts for Preti" --intended_for--> "Guercino".
                 continue
        
        current_subject = sub
        
        # --- OBJECT SPLITTING ---
        
        # Rule 1: Locations with ' and '
        if predicate == 'located_in' and ' and ' in obj:
            parts = obj.split(' and ')
            for p in parts:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': 'located_in',
                    'Object': clean_object(p), 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
            continue

        # Rule 2: Collaborations with ' and '
        if predicate == 'collaborated_on' and ' and ' in obj:
            parts = obj.split(' and ')
            for p in parts:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': 'collaborated_on',
                    'Object': clean_object(p), 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
            continue

        # Rule 3: "See under"
        if str(obj).lower().startswith('see under '):
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': 'refer_to',
                'Object': obj[10:].strip(), 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            continue

        # Rule 4: Descriptive Lists (portraits of X and Y)
        lower_obj = obj.lower()
        matched_prefix = False
        for prefix in LIST_PREFIXES:
            if lower_obj.startswith(prefix + ' ') and ' and ' in lower_obj:
                actual_prefix = obj[:len(prefix)]
                split_objs = split_list(obj, actual_prefix)
                for new_obj in split_objs:
                    final_rows.append({
                        'Subject': current_subject, 'Subject QID': row['Subject QID'],
                        'Predicate': predicate,
                        'Object': new_obj, 'Object QID': row['Object QID'],
                        'Source_Raw': source_raw
                    })
                matched_prefix = True
                break
        if matched_prefix:
            continue

        # Rule 5: Dedications
        dedication_match = re.match(r'dedication of (.+) to (.+)', obj, re.IGNORECASE)
        if dedication_match:
            work = dedication_match.group(1).strip()
            recipient = dedication_match.group(2).strip()
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': 'dedicated_to',
                'Object': recipient, 'Object QID': '/',
                'Source_Raw': source_raw
            })
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': predicate, 
                'Object': f"dedication of {work}", 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            continue

        # Rule 7: Adj + Adj + Noun
        adj_noun_match = re.match(r'^([A-Z][a-z]+) and ([A-Z][a-z]+) ([a-z]+s)$', obj)
        if adj_noun_match:
            adj1 = adj_noun_match.group(1)
            adj2 = adj_noun_match.group(2)
            noun = adj_noun_match.group(3)
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': predicate,
                'Object': f"{adj1} {noun}", 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': predicate,
                'Object': f"{adj2} {noun}", 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            continue

        # Rule 8: Known compound objects
        if obj in ['medals and gems', 'paintings and caricatures', 'library and pictures', 'drawings and prints']:
             parts = obj.split(' and ')
             for p in parts:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': predicate,
                    'Object': p.strip(), 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
             continue
             
        # Rule 9: Simple "Name1 and Name2"
        match_obj_names = re.match(r'^([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)$', obj)
        if match_obj_names:
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': predicate,
                'Object': match_obj_names.group(1), 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            final_rows.append({
                'Subject': current_subject, 'Subject QID': row['Subject QID'],
                'Predicate': predicate,
                'Object': match_obj_names.group(2), 'Object QID': row['Object QID'],
                'Source_Raw': source_raw
            })
            continue

        # Rule 10: Compound Noun Prep
        split_objs = split_compound_noun_prep(obj)
        if len(split_objs) > 1:
            for new_obj in split_objs:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': predicate,
                    'Object': new_obj, 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
            continue

        # Rule 11: Noun Prep List
        split_objs = split_noun_prep_list(obj)
        if len(split_objs) > 1:
            for new_obj in split_objs:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': predicate,
                    'Object': new_obj, 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
            continue
            
        # Rule 12: Pure List
        split_objs = split_pure_list(obj)
        if len(split_objs) > 1:
            for new_obj in split_objs:
                final_rows.append({
                    'Subject': current_subject, 'Subject QID': row['Subject QID'],
                    'Predicate': predicate,
                    'Object': new_obj, 'Object QID': row['Object QID'],
                    'Source_Raw': source_raw
                })
            continue

        # Default
        final_rows.append({
            'Subject': current_subject, 'Subject QID': row['Subject QID'],
            'Predicate': predicate,
            'Object': obj, 'Object QID': row['Object QID'],
            'Source_Raw': source_raw
        })

    return final_rows

def main():
    print(f"Scanning {input_dir}...", flush=True)
    files = glob.glob(os.path.join(input_dir, '*_Triples.csv'))
    print(f"Found {len(files)} files.", flush=True)
    
    total_split = 0
    
    for file_path in files:
        print(f"Refining {os.path.basename(file_path)}...")
        df = pd.read_csv(file_path)
        
        refined_data = []
        original_count = len(df)
        
        for _, row in df.iterrows():
            new_rows = refine_row(row)
            refined_data.extend(new_rows)
            
        new_df = pd.DataFrame(refined_data)
        
        # Re-number the index (序号)
        if '序号' in new_df.columns:
            new_df['序号'] = range(1, len(new_df) + 1)
            
        new_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        diff = len(new_df) - original_count
        if diff > 0:
            print(f"  -> Added {diff} rows (Split/Refined)")
            total_split += diff
        else:
            print("  -> No changes in row count.")

    print(f"Done. Total extra rows generated: {total_split}")

if __name__ == "__main__":
    main()
