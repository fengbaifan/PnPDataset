import pandas as pd
import os
import re
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def parse_candidate(candidate_str):
    # Format: "Q12345 (Label: Description)"
    # We want to extract QID, Label, Description
    # Note: Description might contain parentheses, so we need to be careful.
    # Regex: ^(Q\d+)\s\((.+?):\s*(.*)\)$
    # But sometimes description is empty or format varies slightly if I constructed it manually in previous script.
    # Previous script construction: f"{qid} ({label}: {desc})"
    
    match = re.match(r"^(Q\d+)\s\((.+?):\s*(.*)\)$", candidate_str.strip())
    if match:
        return match.group(1), match.group(2), match.group(3)
    
    # Fallback if no description or colon
    match = re.match(r"^(Q\d+)\s\((.+?)\)$", candidate_str.strip())
    if match:
        return match.group(1), match.group(2), ""
        
    return None, None, None

def refine_matches():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Wikidata_Enriched.csv')
    output_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Wikidata_Refined.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Track changes
    new_matches = 0
    
    for index, row in df.iterrows():
        # Skip if already matched
        if pd.notna(row['Wikidata_QID']) and str(row['Wikidata_QID']).strip() != '':
            continue
            
        candidates_field = str(row.get('Wikidata_Candidates', ''))
        if not candidates_field or candidates_field == 'nan' or candidates_field == 'No match found':
            continue
            
        # Get the first candidate (usually the best ranked by Wikidata)
        first_candidate_str = candidates_field.split('|')[0].strip()
        
        qid, label, desc = parse_candidate(first_candidate_str)
        
        if not qid:
            continue
            
        target_name = str(row['Formal_Full_Name'])
        
        # --- Heuristics for Auto-Acceptance ---
        accept = False
        reason = ""
        
        # 1. High String Similarity (> 0.85)
        sim_score = similarity(target_name, label)
        
        # 2. Substring match (if lengths are close)
        # e.g. "Leonaert Bramer" vs "Leonard Bramer"
        
        if sim_score > 0.85:
            accept = True
            reason = f"High similarity ({sim_score:.2f})"
        elif target_name.lower() in label.lower() or label.lower() in target_name.lower():
            # Only accept substring if it's substantial
            if len(target_name) > 5 and len(label) > 5:
                # Check if it's just a "The" difference
                if abs(len(target_name) - len(label)) < 5:
                    accept = True
                    reason = "Substring match with similar length"
                # Check for "Elder/Younger" distinction which might be dangerous
                elif "elder" in target_name.lower() or "younger" in target_name.lower():
                    # If target specifies generation but label doesn't, be careful.
                    # But if label specifies it and target doesn't?
                    pass
                else:
                    # If similarity is decent (> 0.7) and substring
                    if sim_score > 0.7:
                        accept = True
                        reason = f"Substring + Moderate similarity ({sim_score:.2f})"

        if accept:
            df.at[index, 'Wikidata_QID'] = qid
            df.at[index, 'Wikidata_Label'] = label
            df.at[index, 'Wikidata_Description'] = desc
            df.at[index, 'Match_Type'] = f"Auto-Refined: {reason}" # Update match type for audit
            new_matches += 1
            print(f"[Auto-Accept] '{target_name}' -> '{label}' ({qid}) [{reason}]")
            
    print(f"\nTotal new matches accepted: {new_matches}")
    
    # Save
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved refined list to {output_csv}")

if __name__ == "__main__":
    refine_matches()
