import pandas as pd
import re
import os
import glob

# Configuration
input_dir = r'c:\Users\001\Desktop\14-Relation\05-Cleaned-Index'
output_dir = r'c:\Users\001\Desktop\14-Relation\06-Extraction-Rules'

def clean_text(text):
    if pd.isna(text) or text == '' or str(text).lower() == 'nan':
        return None
    return str(text).strip()

def parse_main_entry(entry):
    """
    Parses 'Name (Identity)' -> Name, Identity
    Returns: name, identity
    """
    if not entry: return None, None
    
    match = re.match(r'(.+?)\s*\((.+?)\)$', entry)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return entry, None

def extract_triples(df):
    triples = []
    
    # Regex Patterns
    # Location: Allow digits, dots, commas, parens, hyphens. Must start with Capital or Digit.
    LOC_PATTERN = r'\bin\s+([A-Z0-9][a-zA-Z0-9\s\.\,\(\)\-]+)'
    # Recipient: Similar to location but for people/entities
    FOR_PATTERN = r'\bfor\s+([A-Z][a-zA-Z0-9\s\.\,\(\)\-]+)'
    
    # Art keywords to identify "created" relations vs generic "sponsored"
    ART_KEYWORDS = ['fresco', 'painting', 'drawing', 'sculpture', 'bust', 'statue', 'altarpiece', 
                    'decoration', 'design', 'work', 'sketch', 'model', 'portrait', 'view', 
                    'capriccio', 'etching', 'engraving', 'print', 'picture', 'monument', 'tomb']

    for idx, row in df.iterrows():
        source_raw = str(idx + 1)
        
        main_entry = clean_text(row.get('Index_Main Entry'))
        location = clean_text(row.get('Index_Location'))
        sub_entry = clean_text(row.get('Index_Sub-entry'))
        detail = clean_text(row.get('Index_Detail'))
        
        if not main_entry:
            continue
            
        # 1. Parse Main Entry Identity
        subject_name, subject_identity = parse_main_entry(main_entry)
        
        if subject_identity:
            triples.append({
                'Subject': subject_name, 'Subject QID': '/',
                'Predicate': 'is',
                'Object': subject_identity, 'Object QID': '/',
                'Source_Raw': source_raw
            })
            
        # 2. Main Entry Location
        if location:
            triples.append({
                'Subject': subject_name, 'Subject QID': '/',
                'Predicate': 'located_in',
                'Object': location, 'Object QID': '/',
                'Source_Raw': source_raw
            })

        # 3. Process Sub-entry / Detail
        texts_to_process = []
        if sub_entry: texts_to_process.append(sub_entry)
        if detail: texts_to_process.append(detail)
        
        for text in texts_to_process:
            # Check for Art Work context
            lower_text = text.lower()
            is_art_work = any(lower_text.startswith(k) for k in ART_KEYWORDS)

            # A. "and Person" -> collaborated_on
            if lower_text.startswith('and '):
                partner = text[4:].strip()
                triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': 'collaborated_on',
                    'Object': partner, 'Object QID': '/',
                    'Source_Raw': source_raw
                })
                continue
                
            # B. "built by", "designed by", "painted by"
            action_match = re.search(r'(.+?)\s+(built|designed|painted|created) by\s+(.+)', text, re.IGNORECASE)
            if action_match:
                obj_phrase = action_match.group(0).strip()
                action = action_match.group(2).lower()
                artist = action_match.group(3).strip()
                pred = action
                
                # Patron commission relation
                triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': 'commissioned',
                    'Object': obj_phrase, 'Object QID': '/',
                    'Source_Raw': source_raw
                })
                
                # Artist creation relation
                triples.append({
                    'Subject': artist, 'Subject QID': '/',
                    'Predicate': pred,
                    'Object': obj_phrase, 'Object QID': '/',
                    'Source_Raw': source_raw
                })
                continue

            # C. "protector of" -> sponsored
            if 'protector of' in lower_text:
                match = re.match(r'(.+?)\s+as protector of', text, re.IGNORECASE)
                if match:
                    person = match.group(1).strip()
                    triples.append({
                        'Subject': person, 'Subject QID': '/',
                        'Predicate': 'sponsored',
                        'Object': subject_name, 'Object QID': '/',
                        'Source_Raw': source_raw
                    })
                    continue
            
            # D. "collection of"
            if 'collection of' in lower_text:
                triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': 'sponsored',
                    'Object': text, 'Object QID': '/',
                    'Source_Raw': source_raw
                })
                continue
                
            # F. "during reign"
            if 'during reign' in lower_text:
                 triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': 'occurred_during',
                    'Object': text, 'Object QID': '/',
                    'Source_Raw': source_raw
                 })
                 continue

            # G. "for [Recipient]"
            for_match = re.search(FOR_PATTERN, text)
            if for_match:
                 recipient = for_match.group(1).strip()
                 # Clean trailing punctuation
                 recipient = recipient.rstrip('.,;()')
                 
                 triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': 'created',
                    'Object': text, 'Object QID': '/',
                    'Source_Raw': source_raw
                 })
                 
                 triples.append({
                    'Subject': text, 'Subject QID': '/',
                    'Predicate': 'intended_for',
                    'Object': recipient, 'Object QID': '/',
                    'Source_Raw': source_raw
                 })
                 continue

            # H. "in [Location]"
            # This logic falls through to allow "Subject -> Text" relation extraction below
            in_match = re.search(LOC_PATTERN, text)
            if in_match:
                loc = in_match.group(1).strip()
                # Exclude pure numbers (years) and "century"
                if not re.match(r'^[\d\s\.\,\-]+$', loc) and 'century' not in loc.lower():
                    loc = loc.rstrip('.,;()')
                    triples.append({
                        'Subject': text, 'Subject QID': '/',
                        'Predicate': 'located_in',
                        'Object': loc, 'Object QID': '/',
                        'Source_Raw': source_raw
                    })

            # E. General relationship (Fallback)
            if text:
                predicate = 'sponsored'
                if subject_name.startswith('Accademia'):
                    predicate = 'sponsored'
                elif is_art_work:
                    predicate = 'created'
                
                triples.append({
                    'Subject': subject_name, 'Subject QID': '/',
                    'Predicate': predicate,
                    'Object': text, 'Object QID': '/',
                    'Source_Raw': source_raw
                })

    return pd.DataFrame(triples)

def main():
    print(f"Scanning {input_dir}...")
    
    # Get all csv files
    files = glob.glob(os.path.join(input_dir, '*.csv'))
    print(f"Found {len(files)} files to process.")

    for file_path in files:
        filename = os.path.basename(file_path)
        # Construct output filename: A_refined.csv -> A_refined_Triples.csv
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_Triples.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing {filename}...")
        
        try:
            df = pd.read_csv(file_path)
            triples_df = extract_triples(df)
            
            # Add Index column
            triples_df.insert(0, '序号', range(1, len(triples_df) + 1))
            
            print(f"Saving {len(triples_df)} triples to {output_path}...")
            triples_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    print("All files processed.")

if __name__ == "__main__":
    main()
