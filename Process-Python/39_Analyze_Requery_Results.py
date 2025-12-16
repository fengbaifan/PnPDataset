import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "09-QID-Crosscheck", "03-Requery_Results.csv")
output_report = os.path.join(base_dir, "09-QID-Crosscheck", "03-Requery_Analysis_Report.txt")

def analyze_results():
    print(f"Loading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except:
        df = pd.read_csv(input_file, encoding='gbk')
        
    total_rows = len(df)
    print(f"Total Rows: {total_rows}")
    
    # 1. Overall Match Statistics
    # Check if Query_QID is not null and not empty
    has_query_result = df['Query_QID'].notna() & (df['Query_QID'] != "")
    match_count = has_query_result.sum()
    match_rate = (match_count / total_rows) * 100
    
    # 2. Confidence Distribution
    # Extract confidence level from Query_Logic string (e.g., "High Confidence - ...")
    def get_confidence(val):
        if pd.isna(val): return "No Result"
        val = str(val)
        if "High Confidence" in val: return "High"
        if "Medium Confidence" in val: return "Medium"
        if "Low Confidence" in val: return "Low"
        if "No results found" in val: return "No Result"
        if "No suitable match" in val: return "No Match"
        return "Other"

    df['Confidence_Level'] = df['Query_Logic'].apply(get_confidence)
    confidence_counts = df['Confidence_Level'].value_counts()
    
    # 3. Comparison with Original QID
    # Ensure QID column exists and handle NaNs
    if 'QID' not in df.columns:
        df['QID'] = None
        
    df['Original_Has_QID'] = df['QID'].notna() & (df['QID'] != "")
    
    # Case A: Original was Empty, New Found (Enrichment)
    newly_found = (~df['Original_Has_QID']) & has_query_result
    newly_found_count = newly_found.sum()
    
    # Case B: Original Existed, New Matches Original (Confirmation)
    # Normalize QIDs for comparison
    df['QID_Clean'] = df['QID'].astype(str).str.strip()
    df['Query_QID_Clean'] = df['Query_QID'].astype(str).str.strip()
    
    confirmed = df['Original_Has_QID'] & has_query_result & (df['QID_Clean'] == df['Query_QID_Clean'])
    confirmed_count = confirmed.sum()
    
    # Case C: Original Existed, New Differs (Conflict)
    conflict = df['Original_Has_QID'] & has_query_result & (df['QID_Clean'] != df['Query_QID_Clean'])
    conflict_count = conflict.sum()
    
    # Case D: Original Existed, New Not Found (Potential Miss)
    missed = df['Original_Has_QID'] & (~has_query_result)
    missed_count = missed.sum()

    # 4. Category Analysis
    cat_stats = df.groupby('Refined_Category')['Confidence_Level'].value_counts().unstack(fill_value=0)
    
    # Generate Report
    report = []
    report.append("=" * 40)
    report.append("ANALYSIS REPORT: Wikidata Requery Results")
    report.append("=" * 40)
    report.append(f"Total Rows Processed: {total_rows}")
    report.append(f"Total Matches Found: {match_count} ({match_rate:.2f}%)")
    report.append("-" * 40)
    report.append("CONFIDENCE DISTRIBUTION:")
    for level, count in confidence_counts.items():
        report.append(f"  {level}: {count} ({(count/total_rows)*100:.1f}%)")
    report.append("-" * 40)
    report.append("COMPARISON WITH ORIGINAL DATA:")
    report.append(f"  1. Enrichment (New QIDs found for empty rows): {newly_found_count}")
    report.append(f"  2. Confirmation (New QID matches Original): {confirmed_count}")
    report.append(f"  3. Conflict (New QID differs from Original): {conflict_count}")
    report.append(f"  4. Missed (Original had QID, New search failed): {missed_count}")
    report.append("-" * 40)
    report.append("CATEGORY PERFORMANCE (Top 10):")
    # Add total column to sort
    cat_stats['Total'] = cat_stats.sum(axis=1)
    cat_stats = cat_stats.sort_values('Total', ascending=False).head(10)
    
    report.append(cat_stats.to_string())
    
    report_text = "\n".join(report)
    print(report_text)
    
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\nReport saved to {output_report}")

if __name__ == "__main__":
    analyze_results()
