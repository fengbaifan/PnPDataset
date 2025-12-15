import pandas as pd

# Load datasets
merged_path = "merged_1_9.csv"
audit_path = "Audit_List_Wikidata_Refined.csv"

try:
    df_merged = pd.read_csv(merged_path)
    # Try reading audit file with different encodings
    try:
        df_audit = pd.read_csv(audit_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df_audit = pd.read_csv(audit_path, encoding='latin1')
        except UnicodeDecodeError:
            df_audit = pd.read_csv(audit_path, encoding='cp1252')
except Exception as e:
    print(f"Error loading files: {e}")
    exit()

print(f"--- Basic Info ---")
print(f"Merged Dataset: {len(df_merged)} rows, Columns: {list(df_merged.columns)}")
print(f"Audit Dataset: {len(df_audit)} rows, Columns: {list(df_audit.columns)}")

# Normalize column names for comparison
# Assuming Index_Entry == Original_Entry
df_audit_renamed = df_audit.rename(columns={
    'Index_Entry': 'Original_Entry',
    'Formal_Full_Name': 'Refined_Formal_Name',
    'Normalization_Category': 'Refined_Category'
})

# 1. Compare Entry Counts
merged_entries = set(df_merged['Original_Entry'].dropna().astype(str).str.strip())
audit_entries = set(df_audit_renamed['Original_Entry'].dropna().astype(str).str.strip())

common_entries = merged_entries.intersection(audit_entries)
only_in_merged = merged_entries - audit_entries
only_in_audit = audit_entries - merged_entries

print(f"\n--- Entry Overlap (based on Original_Entry) ---")
print(f"Unique entries in Merged: {len(merged_entries)}")
print(f"Unique entries in Audit: {len(audit_entries)}")
print(f"Common entries: {len(common_entries)}")
print(f"Only in Merged: {len(only_in_merged)}")
print(f"Only in Audit: {len(only_in_audit)}")

if len(only_in_merged) > 0:
    print(f"Examples only in Merged: {list(only_in_merged)[:5]}")
if len(only_in_audit) > 0:
    print(f"Examples only in Audit: {list(only_in_audit)[:5]}")

# 2. Compare Content for Common Entries
print(f"\n--- Content Comparison for Common Entries ---")
# Merge on Original_Entry to compare other columns
comparison = pd.merge(
    df_merged, 
    df_audit_renamed, 
    on='Original_Entry', 
    how='inner', 
    suffixes=('_merged', '_audit')
)

# Check for differences in Formal Name
# Fill NaNs with empty string for comparison
comparison['Refined_Formal_Name_merged'] = comparison['Refined_Formal_Name_merged'].fillna('').astype(str).str.strip()
comparison['Refined_Formal_Name_audit'] = comparison['Refined_Formal_Name_audit'].fillna('').astype(str).str.strip()

name_diff = comparison[comparison['Refined_Formal_Name_merged'] != comparison['Refined_Formal_Name_audit']]
print(f"Entries with different Formal Names: {len(name_diff)}")
if len(name_diff) > 0:
    print(name_diff[['Original_Entry', 'Refined_Formal_Name_merged', 'Refined_Formal_Name_audit']].head(5).to_string())

# Check for differences in Category
comparison['Refined_Category_merged'] = comparison['Refined_Category_merged'].fillna('').astype(str).str.strip()
comparison['Refined_Category_audit'] = comparison['Refined_Category_audit'].fillna('').astype(str).str.strip()

cat_diff = comparison[comparison['Refined_Category_merged'] != comparison['Refined_Category_audit']]
print(f"\nEntries with different Categories: {len(cat_diff)}")
if len(cat_diff) > 0:
    print(cat_diff[['Original_Entry', 'Refined_Category_merged', 'Refined_Category_audit']].head(5).to_string())

# Check for empty values in Audit that are filled in Merged
empty_in_audit_filled_in_merged = comparison[
    (comparison['Refined_Formal_Name_audit'] == '') & 
    (comparison['Refined_Formal_Name_merged'] != '')
]
print(f"\nEntries empty in Audit but filled in Merged: {len(empty_in_audit_filled_in_merged)}")
