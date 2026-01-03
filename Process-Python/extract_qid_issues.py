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

# 1. Identify rows with multiple QIDs in 'Original-QID'
# We look for semicolons ';' which typically separate multiple QIDs
# We also handle non-string types just in case
def has_multiple_qids(val):
    if pd.isna(val):
        return False
    return ';' in str(val)

multiple_qid_mask = df['Original-QID'].apply(has_multiple_qids)
multiple_qid_df = df[multiple_qid_mask]

# 2. Identify rows with empty 'Original-QID'
# We check for NaN or empty strings
missing_qid_mask = df['Original-QID'].isna() | (df['Original-QID'].astype(str).str.strip() == '')
missing_qid_df = df[missing_qid_mask]

# Define output files
output_multiple = os.path.join(output_dir, "01-Multiple_QIDs.csv")
output_missing = os.path.join(output_dir, "02-Missing_QIDs.csv")

# Save to CSV
multiple_qid_df.to_csv(output_multiple, index=False)
missing_qid_df.to_csv(output_missing, index=False)

# Print summary
print(f"Processed {input_file}")
print(f"Found {len(multiple_qid_df)} rows with multiple QIDs.")
print(f"Found {len(missing_qid_df)} rows with missing QIDs.")
print(f"Saved multiple QIDs to: {output_multiple}")
print(f"Saved missing QIDs to: {output_missing}")
