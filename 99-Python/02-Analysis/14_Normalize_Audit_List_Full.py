import pandas as pd
import os
import re

# --- Configuration & Dictionaries ---

# Titles to strip (Person)
TITLES = [
    'Sir', 'Lord', 'Lady', 'Duke', 'Duchess', 'Count', 'Countess', 'Earl', 'Baron', 
    'Prince', 'Princess', 'King', 'Queen', 'Cardinal', 'Pope', 'Bishop', 'Abbot', 
    'Fra', 'Don', 'Donna', 'Marchese', 'Marchesa', 'Cavaliere', 'Abate', 'Monsignor',
    'President', 'Président', 'Mme', 'Mlle', 'Mr', 'Mrs', 'Dr', 'Prof', 'Archbishop-Elector'
]

# Nickname Mapping (Based on research)
NICKNAMES = {
    'baciccio': 'Giovanni Battista Gaulli',
    'baciccia': 'Giovanni Battista Gaulli',
    'monsù desiderio': 'François de Nomé',
    'il guercino': 'Giovanni Francesco Barbieri',
    'guercino': 'Giovanni Francesco Barbieri',
    'canaletto': 'Giovanni Antonio Canal',
    'tintoretto': 'Jacopo Robusti',
    'domenichino': 'Domenico Zampieri',
    'parmigianino': 'Girolamo Francesco Maria Mazzola',
    'pontormo': 'Jacopo Carucci',
    'bronzino': 'Agnolo di Cosimo',
    'veronese': 'Paolo Caliari',
    'bernini': 'Gian Lorenzo Bernini', # Often just listed as Bernini
    'borromini': 'Francesco Borromini'
}

# Place/Building Rules
# "X palace" -> "Palazzo X"
# "X villa" -> "Villa X"

# --- Normalization Functions ---

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.strip().strip('"').strip("'")
    text = " ".join(text.split())
    return text

def remove_parentheses(name):
    # Remove content in parentheses e.g. (Pope Clement XI)
    return re.sub(r'\(.*?\)', '', name).strip()

def strip_titles(name):
    for title in TITLES:
        pattern = r'\b' + re.escape(title) + r'\b\.?'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    return " ".join(name.split())

def flip_name(name):
    if "," in name:
        parts = name.split(",", 1)
        if len(parts) == 2:
            # Handle "Acqua, Cristoforo dall'" -> "Cristoforo dall' Acqua"
            # Handle "Bacon, Sir Francis" -> "Sir Francis Bacon"
            return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def normalize_person_full(name):
    # 1. Check Nickname Dictionary first (Exact match on raw or simple clean)
    simple_name = name.lower().strip().strip("'").strip('"')
    if simple_name in NICKNAMES:
        return NICKNAMES[simple_name]
    
    # 2. Remove Parentheses (Roles, Aliases)
    # e.g. "Albani, Gianfrancesco (Pope Clement XI)" -> "Albani, Gianfrancesco"
    name = remove_parentheses(name)
    
    # 3. Flip Name (Last, First -> First Last)
    name = flip_name(name)
    
    # 4. Strip Titles
    # e.g. "Cardinal Annibale Albani" -> "Annibale Albani"
    name = strip_titles(name)
    
    # 5. Clean extra spaces
    name = " ".join(name.split())
    
    return name

def normalize_place_full(name):
    # 1. Remove Parentheses
    # e.g. "Alticchiero (Querini villa)" -> "Alticchiero"
    # But wait, research said "Alticchiero (Querini villa)" -> "Villa Alticchiero"
    # This is tricky. Let's try to detect "villa" or "palace" inside parens or outside.
    
    lower_name = name.lower()
    
    # Special Case: "Alticchiero (Querini villa)"
    if 'alticchiero' in lower_name and 'villa' in lower_name:
        return "Villa Alticchiero"
    
    name = remove_parentheses(name)
    
    # 2. Standardize Building Types (English -> Italian)
    # "X Palace" -> "Palazzo X"
    if lower_name.endswith(' palace'):
        # Extract X
        core = name[:-7].strip() # remove " palace"
        return f"Palazzo {core}"
    
    # "X Villa" -> "Villa X" (if not already Villa X)
    if lower_name.endswith(' villa'):
        core = name[:-6].strip()
        return f"Villa {core}"
        
    # 3. Expand Abbreviations
    name = name.replace("S.", "San").replace("St.", "Saint")
    
    return name.strip()

def normalize_work_full(name):
    # 1. Remove quotes
    name = clean_text(name)
    
    # 2. Expand Abbreviations common in titles
    name = name.replace("St.", "Saint").replace("S.", "San")
    
    # 3. Handle Inversions "Artists, status of" -> "Status of artists"
    if "," in name:
        parts = name.split(",", 1)
        p1 = parts[0].strip()
        p2 = parts[1].strip()
        
        # Heuristic: if p2 is short and looks like a prefix?
        # "Artists, status of" -> "Status of Artists"
        # "Magi, Adoration of the" -> "Adoration of the Magi"
        if p2.lower().startswith(('status of', 'development of', 'adoration of', 'portrait of', 'view of')):
             return f"{p2} {p1}"
             
    return name

def normalize_audit_list_comprehensive():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Combined.csv')
    output_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Normalized_Full.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    df['Formal_Full_Name'] = ''
    df['Normalization_Category'] = ''
    
    for index, row in df.iterrows():
        # Determine source info
        raw_name = ""
        category = "Unknown"
        
        # Logic to determine Category and Raw Name
        extraction_reason = str(row.get('Extraction_Reason', ''))
        
        if 'Index' in extraction_reason:
            raw_name = str(row.get('Index_Entry', ''))
            cidoc = str(row.get('CIDOC_Type', ''))
            
            if cidoc == 'E21 Person':
                category = 'Person'
            elif cidoc in ['E53 Place', 'E74 Group']:
                category = 'Place'
            else:
                category = 'Work' # E22, E28, E55
                
        else: # Manual Source
            raw_name = str(row.get('Manual_Name', ''))
            file_code = str(row.get('File_Code', '')).lower()
            
            if 'name' in file_code: 
                category = 'Person'
            elif 'gio' in file_code: 
                category = 'Place'
            elif 'work' in file_code: 
                category = 'Work'
            else:
                category = 'Work' # Default fallback
            
        if not raw_name or raw_name == 'nan': continue
        
        # Apply Logic based on Category
        formal_name = raw_name
        
        if category == 'Person':
            formal_name = normalize_person_full(raw_name)
        elif category == 'Place':
            formal_name = normalize_place_full(raw_name)
        elif category == 'Work':
            # Special check: sometimes People or Places are misclassified as Works in Index
            # We do a quick check for obvious misclassifications
            lower_raw = raw_name.lower()
            
            # Use regex for titles to avoid substring matches (e.g. "King" in "Seeking")
            title_pattern = r'\b(' + '|'.join(re.escape(t.lower()) for t in TITLES) + r')\b'
            has_title = bool(re.search(title_pattern, lower_raw))
            
            # If it contains "Palace" or "Villa", treat as Place
            if 'palace' in lower_raw or 'villa' in lower_raw:
                formal_name = normalize_place_full(raw_name)
                category = 'Place (Reclassified)'
            # If it contains noble titles, treat as Person
            elif has_title:
                formal_name = normalize_person_full(raw_name)
                category = 'Person (Reclassified)'
            else:
                formal_name = normalize_work_full(raw_name)
        
        # Capitalize first letter
        if formal_name and formal_name[0].islower():
            formal_name = formal_name[0].upper() + formal_name[1:]
            
        df.at[index, 'Formal_Full_Name'] = formal_name
        df.at[index, 'Normalization_Category'] = category
        
    # Save
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved comprehensive normalized list to: {output_csv}")
    
    # Preview
    print("\n--- Sample Formal Names (Index Source) ---")
    print(df[df['Index_Entry'].notna() & (df['Index_Entry'] != '')][['Index_Entry', 'Normalization_Category', 'Formal_Full_Name']].head(10))

    print("\n--- Sample Formal Names (Manual Source) ---")
    print(df[df['Manual_Name'].notna() & (df['Manual_Name'] != '')][['Manual_Name', 'Normalization_Category', 'Formal_Full_Name']].head(10))

if __name__ == "__main__":
    normalize_audit_list_comprehensive()
