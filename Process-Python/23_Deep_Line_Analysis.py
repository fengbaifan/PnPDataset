import pandas as pd
import re
import os
from collections import defaultdict
import difflib

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_report = os.path.join(base_dir, "Process-Python", "02-Analysis", "Deep_Line_Analysis_Report.txt")
output_csv = os.path.join(base_dir, "Process-Python", "02-Analysis", "Deep_Analysis_Details.csv")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_report), exist_ok=True)

def get_similarity(s1, s2):
    return difflib.SequenceMatcher(None, str(s1).lower(), str(s2).lower()).ratio()

def analyze_line_by_line():
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(input_file, encoding='gbk')

    print(f"Processing {len(df)} rows...")

    # Storage for findings
    inconsistent_categories = defaultdict(set)
    ocr_suspects = []
    unstructured_notes = []
    complex_notes = []
    
    # New columns for detailed CSV
    df['Analysis_Tag'] = ''
    df['Similarity_Score'] = 0.0
    df['Issue_Flag'] = ''

    for index, row in df.iterrows():
        orig = str(row['Original_Entry']).strip()
        refined = str(row['Refined_Formal_Name']).strip()
        cat = str(row['Refined_Category']).strip()
        note = str(row['Status/Notes']).strip()

        # 1. Consistency Check
        inconsistent_categories[refined].add(cat)

        # 2. Similarity / OCR Check
        sim_score = get_similarity(orig, refined)
        df.at[index, 'Similarity_Score'] = round(sim_score, 2)
        
        # If similarity is low but not extremely low (which might indicate a complete rename/alias), flag it
        # Low similarity + No "Disambiguation" or "Alias" in note -> Potential OCR mess or wrong match
        if sim_score < 0.6 and sim_score > 0.1:
            if "Disambiguation" not in note and "Nick" not in note and "alias" not in note.lower():
                ocr_suspects.append({
                    'Row': index + 1,
                    'Original': orig,
                    'Refined': refined,
                    'Score': f"{sim_score:.2f}",
                    'Note': note
                })
                df.at[index, 'Issue_Flag'] += 'Low_Similarity; '

        # 3. Note Analysis
        if pd.isna(row['Status/Notes']) or row['Status/Notes'] == 'nan':
            df.at[index, 'Analysis_Tag'] = 'Missing_Note'
        elif '[' in note and ']' in note:
            # Extract tag
            tag_match = re.search(r'\[(.*?)\]', note)
            if tag_match:
                df.at[index, 'Analysis_Tag'] = tag_match.group(1)
        else:
            # Unstructured
            df.at[index, 'Analysis_Tag'] = 'Unstructured'
            unstructured_notes.append(note)
            
            # Try to guess content
            if any(x in note.lower() for x in ['painter', 'artist', 'sculptor', 'architect']):
                df.at[index, 'Issue_Flag'] += 'Role_Description; '
            elif any(x in note.lower() for x in ['city', 'town', 'region', 'church', 'palace']):
                df.at[index, 'Issue_Flag'] += 'Place_Description; '

    # Generate Report
    report_lines = []
    report_lines.append("=== Deep Line-by-Line Analysis Report ===")
    report_lines.append(f"Total Rows Processed: {len(df)}")
    report_lines.append("-" * 30)

    # Report 1: Inconsistent Categories
    multi_cat_entities = {k: v for k, v in inconsistent_categories.items() if len(v) > 1}
    report_lines.append(f"\n[1. Inconsistent Categories] (Same name, different categories)")
    report_lines.append(f"Found {len(multi_cat_entities)} entities with multiple categories.")
    for name, cats in list(multi_cat_entities.items())[:20]:
        report_lines.append(f"  - {name}: {', '.join(cats)}")
    if len(multi_cat_entities) > 20:
        report_lines.append(f"  ... and {len(multi_cat_entities) - 20} more.")

    # Report 2: Potential OCR/Mapping Issues
    report_lines.append(f"\n[2. Low Similarity Mappings] (Potential OCR errors or aggressive normalization)")
    report_lines.append(f"Found {len(ocr_suspects)} entries with similarity < 0.6 (excluding known aliases).")
    for item in ocr_suspects[:20]:
        report_lines.append(f"  - Row {item['Row']}: '{item['Original']}' -> '{item['Refined']}' (Score: {item['Score']}) | Note: {item['Note']}")

    # Report 3: Unstructured Notes Analysis
    report_lines.append(f"\n[3. Unstructured Notes]")
    report_lines.append(f"Found {len(unstructured_notes)} entries with unstructured notes.")
    report_lines.append("Sample of unstructured notes:")
    for n in unstructured_notes[:10]:
        report_lines.append(f"  - {n}")

    # Save Report
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    # Save Detailed CSV
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')

    print(f"Analysis complete.")
    print(f"Summary Report: {output_report}")
    print(f"Detailed CSV: {output_csv}")
    print('\n'.join(report_lines[:40])) # Print first 40 lines to terminal

if __name__ == "__main__":
    analyze_line_by_line()
