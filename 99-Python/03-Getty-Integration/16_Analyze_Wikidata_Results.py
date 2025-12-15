import pandas as pd
import os

def analyze_wikidata_results():
    base_dir = r'c:\Users\001\Desktop\Github-Project\PnPDataset'
    input_csv = os.path.join(base_dir, r'06-Crosscheck\Audit_List_Wikidata_Enriched.csv')
    
    if not os.path.exists(input_csv):
        print(f"File not found: {input_csv}")
        return

    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    total_rows = len(df)
    
    # 1. Overall Statistics
    matched_qid = df[df['Wikidata_QID'].notna() & (df['Wikidata_QID'] != '')]
    num_matched = len(matched_qid)
    
    # Candidates found but no QID assigned (Ambiguous or no exact match)
    # Note: 'Wikidata_Candidates' might be "No match found" string, so we need to check content
    has_candidates = df[
        (df['Wikidata_QID'].isna() | (df['Wikidata_QID'] == '')) & 
        (df['Wikidata_Candidates'].notna()) & 
        (df['Wikidata_Candidates'] != 'No match found')
    ]
    num_candidates = len(has_candidates)
    
    no_match = df[
        (df['Wikidata_QID'].isna() | (df['Wikidata_QID'] == '')) & 
        ((df['Wikidata_Candidates'].isna()) | (df['Wikidata_Candidates'] == 'No match found'))
    ]
    num_no_match = len(no_match)
    
    print("\n" + "="*40)
    print("WIKIDATA MATCHING ANALYSIS REPORT")
    print("="*40)
    print(f"Total Items Processed: {total_rows}")
    print(f"Exact/High Confidence Matches (QID): {num_matched} ({num_matched/total_rows*100:.1f}%)")
    print(f"Potential/Ambiguous Matches:         {num_candidates} ({num_candidates/total_rows*100:.1f}%)")
    print(f"No Match Found:                      {num_no_match} ({num_no_match/total_rows*100:.1f}%)")
    
    # 2. Category Breakdown
    print("\n" + "-"*40)
    print("BREAKDOWN BY CATEGORY")
    print("-"*40)
    
    # Clean up category names for grouping
    df['Category_Clean'] = df['Normalization_Category'].replace({
        'Person (Reclassified)': 'Person',
        'Place (Reclassified)': 'Place'
    })
    
    stats = df.groupby('Category_Clean').apply(lambda x: pd.Series({
        'Total': len(x),
        'Matched': len(x[x['Wikidata_QID'].notna()]),
        'Potential': len(x[
            (x['Wikidata_QID'].isna()) & 
            (x['Wikidata_Candidates'].notna()) & 
            (x['Wikidata_Candidates'] != 'No match found')
        ])
    }))
    
    stats['Match Rate'] = (stats['Matched'] / stats['Total'] * 100).round(1)
    print(stats)
    
    # 3. Examples
    print("\n" + "-"*40)
    print("EXAMPLES: SUCCESSFUL MATCHES")
    print("-"*40)
    print(matched_qid[['Formal_Full_Name', 'Normalization_Category', 'Wikidata_QID', 'Wikidata_Label']].head(5).to_string(index=False))
    
    print("\n" + "-"*40)
    print("EXAMPLES: POTENTIAL MATCHES (Candidates found but no QID)")
    print("-"*40)
    # Show candidates truncated
    pd.set_option('display.max_colwidth', 100)
    print(has_candidates[['Formal_Full_Name', 'Normalization_Category', 'Wikidata_Candidates']].head(5).to_string(index=False))

    print("\n" + "-"*40)
    print("EXAMPLES: NO MATCH FOUND")
    print("-"*40)
    print(no_match[['Formal_Full_Name', 'Normalization_Category']].head(5).to_string(index=False))

if __name__ == "__main__":
    analyze_wikidata_results()
