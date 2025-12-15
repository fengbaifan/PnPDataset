import pandas as pd
import os
import re

# --- Configuration & Dictionaries ---

TITLES = [
    'Sir', 'Lord', 'Lady', 'Duke', 'Duchess', 'Count', 'Countess', 'Earl', 'Baron', 
    'Prince', 'Princess', 'King', 'Queen', 'Cardinal', 'Pope', 'Bishop', 'Abbot', 
    'Fra', 'Don', 'Donna', 'Marchese', 'Marchesa', 'Cavaliere', 'Abate', 'Monsignor',
    'President', 'Président', 'Mme', 'Mlle', 'Mr', 'Mrs', 'Dr', 'Prof'
]

# Suffixes to remove or handle
SUFFIXES = [
    r'\(.*?\)', # Remove content in parentheses e.g. (Pope Clement XI)
    r'\[.*?\]', # Remove content in brackets
]

# --- Normalization Functions ---

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.strip().strip('"').strip("'")
    text = " ".join(text.split())
    return text

def strip_titles(name):
    # Sort titles by length descending to match "Grand Duke" before "Duke" if we had multi-word titles
    # For now TITLES are mostly single words.
    for title in TITLES:
        # Pattern: Word boundary + Title + (Space or End or Dot)
        pattern = r'\b' + re.escape(title) + r'\b\.?'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    return " ".join(name.split())

def remove_parentheses(name):
    for pattern in SUFFIXES:
        name = re.sub(pattern, '', name)
    return " ".join(name.split())

def flip_name(name):
    if "," in name:
        parts = name.split(",", 1)
        if len(parts) == 2:
            return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def normalize_person_advanced(name):
    # 1. Remove parentheses content (often roles or alternate names in Index)
    # e.g. "Albani, Gianfrancesco (Pope Clement XI)" -> "Albani, Gianfrancesco"
    name = remove_parentheses(name)
    
    # 2. Flip if comma exists
    if "," in name:
        name = flip_name(name)
    
    # 3. Strip Titles
    name = strip_titles(name)
    
    # 4. Remove 'de', 'di', 'da' prefix if it starts the name after flip? 
    # Actually, "da Vinci" is correct. But "d'Adda" -> "Adda"? 
    # Let's keep particles for now as ULAN often includes them.
    
    return name.strip()

def normalize_place_group_advanced(name):
    # 1. Remove parentheses
    name = remove_parentheses(name)
    
    # 2. Expand common abbreviations (reusing logic if needed, but simple clean first)
    name = name.replace("S.", "San").replace("St.", "Saint")
    
    return name.strip()

def normalize_audit_list():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Combined.csv')
    output_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Normalized.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # New column for Normalized Name
    df['Normalized_Name'] = ''
    
    count = 0
    for index, row in df.iterrows():
        # Determine source name
        raw_name = ""
        c_type = ""
        
        if 'Index' in str(row.get('Extraction_Reason', '')):
            raw_name = str(row.get('Index_Entry', ''))
            c_type = str(row.get('CIDOC_Type', ''))
        else:
            raw_name = str(row.get('Manual_Name', ''))
            # Infer type from file code if possible, or default
            file_code = str(row.get('File_Code', ''))
            if 'name' in file_code: c_type = 'E21 Person'
            elif 'gio' in file_code: c_type = 'E53 Place'
            else: c_type = 'E22 Man-Made Object'
            
        if not raw_name or raw_name == 'nan': continue
        
        # Apply Normalization
        norm_name = raw_name
        
        if c_type == 'E21 Person':
            norm_name = normalize_person_advanced(raw_name)
        elif c_type in ['E53 Place', 'E74 Group']:
            norm_name = normalize_place_group_advanced(raw_name)
        else:
            # Basic clean for others
            norm_name = remove_parentheses(raw_name)
            
        df.at[index, 'Normalized_Name'] = norm_name
        count += 1
        
    print(f"Normalized {count} entries.")
    
    # Save
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Saved normalized list to: {output_csv}")
    
    # Preview some changes
    print("\n--- Sample Normalizations ---")
    sample = df[df['Index_Entry'] != df['Normalized_Name']].head(10)
    if not sample.empty:
        print(sample[['Index_Entry', 'Normalized_Name']])

if __name__ == "__main__":
    normalize_audit_list()
