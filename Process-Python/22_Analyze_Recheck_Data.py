import pandas as pd
import os
import re

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset"
input_file = os.path.join(base_dir, "08-Recheck", "01-Merged_Recheck.csv")
output_report = os.path.join(base_dir, "Process-Python", "02-Analysis", "Recheck_Analysis_Report.txt")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_report), exist_ok=True)

def analyze_recheck_data():
    print(f"Loading data from {input_file}...")
    
    # Try reading with different encodings
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(input_file, encoding='gbk')
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    print(f"Total rows loaded: {len(df)}")
    
    # Initialize report content
    report_lines = []
    report_lines.append("=== Recheck Data Analysis Report ===")
    report_lines.append(f"Total Entries: {len(df)}")
    report_lines.append("-" * 30)

    # 1. Column Existence Check
    expected_cols = ['Original_Entry', 'Refined_Formal_Name', 'Refined_Category', 'Status/Notes']
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        report_lines.append(f"WARNING: Missing columns: {missing_cols}")
        # Adjust if columns are missing to prevent crash
        available_cols = [c for c in expected_cols if c in df.columns]
    else:
        available_cols = expected_cols

    # 2. Category Distribution
    if 'Refined_Category' in df.columns:
        cat_counts = df['Refined_Category'].value_counts()
        report_lines.append("\n[Category Distribution]")
        for cat, count in cat_counts.items():
            report_lines.append(f"  - {cat}: {count} ({count/len(df)*100:.1f}%)")
    
    # 3. Status/Notes Analysis
    if 'Status/Notes' in df.columns:
        # Extract tags like [Validation], [Disambiguation], etc.
        def extract_tag(text):
            if pd.isna(text): return "No Note"
            match = re.search(r'\[(.*?)\]', str(text))
            return match.group(1) if match else "Other Note"

        df['Note_Tag'] = df['Status/Notes'].apply(extract_tag)
        tag_counts = df['Note_Tag'].value_counts()
        
        report_lines.append("\n[Note Type Distribution]")
        for tag, count in tag_counts.items():
            report_lines.append(f"  - {tag}: {count} ({count/len(df)*100:.1f}%)")

    # 4. Missing Values
    report_lines.append("\n[Missing Values]")
    for col in available_cols:
        missing = df[col].isna().sum()
        if missing > 0:
            report_lines.append(f"  - {col}: {missing} missing")
        else:
            report_lines.append(f"  - {col}: Complete")

    # 5. Duplicates Analysis
    if 'Refined_Formal_Name' in df.columns:
        dupes = df[df.duplicated(subset=['Refined_Formal_Name'], keep=False)]
        unique_dupes = dupes['Refined_Formal_Name'].nunique()
        report_lines.append(f"\n[Duplicate Analysis]")
        report_lines.append(f"  - Duplicate Refined Names (entries appearing >1 time): {unique_dupes}")
        
        if unique_dupes > 0:
            report_lines.append("  - Top 5 Duplicates:")
            top_dupes = dupes['Refined_Formal_Name'].value_counts().head(5)
            for name, count in top_dupes.items():
                report_lines.append(f"    * {name}: {count} times")

    # 6. Content Sampling (Short vs Long names)
    if 'Refined_Formal_Name' in df.columns:
        df['Name_Length'] = df['Refined_Formal_Name'].astype(str).apply(len)
        avg_len = df['Name_Length'].mean()
        max_len = df['Name_Length'].max()
        report_lines.append(f"\n[Name Length Stats]")
        report_lines.append(f"  - Average Length: {avg_len:.1f} chars")
        report_lines.append(f"  - Max Length: {max_len} chars")

    # Save Report
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Analysis complete. Report saved to: {output_report}")
    print('\n'.join(report_lines))

if __name__ == "__main__":
    analyze_recheck_data()
