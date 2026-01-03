import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset\09-MissingQID-LLM-Fillin"
input_file = os.path.join(base_dir, r"04-QID-Combine ORGfile\07-Requery_Filled_Combined.csv")
output_dir = os.path.join(base_dir, r"05-MissingQID+04Requery")

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Read the CSV
df = pd.read_csv(input_file)

# Helper to check if a value is "present" (not NaN and not empty string)
def is_present(val):
    if pd.isna(val):
        return False
    return str(val).strip() != ''

# 1. Identify rows with multiple QIDs in 'Original-QID' (using ; or ,)
def has_multiple_in_cell(val):
    if not is_present(val):
        return False
    s = str(val)
    return ';' in s or ',' in s

multiple_in_cell_mask = df['Original-QID'].apply(has_multiple_in_cell)

# 2. Identify rows with QIDs in multiple columns (Original AND Second/LLM)
# This corresponds to "2 QIDs" across columns
double_column_mask = df.apply(lambda row: is_present(row['Original-QID']) and (is_present(row['Second-Query_QID']) or is_present(row['LLM-Fillin_QID'])), axis=1)

# Combine "2 QIDs" cases
two_qids_mask = multiple_in_cell_mask | double_column_mask
two_qids_df = df[two_qids_mask]

# 3. Identify rows with TOTALLY missing QIDs (All QID columns are empty)
missing_qid_mask = df.apply(lambda row: not is_present(row['Original-QID']) and not is_present(row['Second-Query_QID']) and not is_present(row['LLM-Fillin_QID']), axis=1)
missing_qid_df = df[missing_qid_mask]

# Define output files
output_two_qids = os.path.join(output_dir, "01-Rows_With_Two_Or_More_QIDs.csv")
output_missing = os.path.join(output_dir, "02-Rows_With_Missing_QIDs.csv")

# Save to CSV
two_qids_df.to_csv(output_two_qids, index=False)
missing_qid_df.to_csv(output_missing, index=False)

# Print summary
print(f"Processed {input_file}")
print(f"Found {len(two_qids_df)} rows with 2+ QIDs (in cell or across columns).")
print(f"Found {len(missing_qid_df)} rows with totally missing QIDs.")
print(f"Saved 2+ QIDs to: {output_two_qids}")
print(f"Saved missing QIDs to: {output_missing}")
