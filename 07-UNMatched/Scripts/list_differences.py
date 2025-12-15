import pandas as pd

# Load datasets with encoding handling
merged_path = "merged_1_9.csv"
audit_path = "Audit_List_Wikidata_Refined.csv"

try:
    df_merged = pd.read_csv(merged_path)
    try:
        df_audit = pd.read_csv(audit_path, encoding='utf-8')
    except UnicodeDecodeError:
        df_audit = pd.read_csv(audit_path, encoding='latin1')
except Exception as e:
    print(f"Error loading files: {e}")
    exit()

# Rename columns for consistency
df_audit_renamed = df_audit.rename(columns={
    'Index_Entry': 'Original_Entry',
    'Formal_Full_Name': 'Refined_Formal_Name',
    'Normalization_Category': 'Refined_Category'
})

# Get sets of Original_Entry
merged_entries = set(df_merged['Original_Entry'].dropna().astype(str).str.strip())
audit_entries = set(df_audit_renamed['Original_Entry'].dropna().astype(str).str.strip())

only_in_merged = sorted(list(merged_entries - audit_entries))
only_in_audit = sorted(list(audit_entries - merged_entries))

print("--- Entries ONLY in Merged Dataset (Likely Encoding Issues) ---")
for entry in only_in_merged:
    print(entry)

print("\n--- Entries ONLY in Audit Dataset ---")
for entry in only_in_audit:
    print(entry)
