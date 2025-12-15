import pandas as pd

# Load the final dataset
file_path = "merged_1_9_final.csv"
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

print("--- Split Items (New Entries) ---")
# Filter for rows where Status/Notes indicates a split
split_items = df[df['Status/Notes'].astype(str).str.contains('\[Split\]', regex=True)]
if not split_items.empty:
    # Show relevant columns
    print(split_items[['Original_Entry', 'Refined_Formal_Name', 'Refined_Category']].to_string())
else:
    print("No split items found.")

print("\n--- Removed Duplicates (Reconstruction) ---")
# Since we already removed them, we can't query the final DF.
# But we know exactly which ones were removed from previous analysis.
# We will list them manually based on the known duplicates.

duplicates_list = [
    {"Original": "Altar of Friendship", "Name": "Altar of Friendship (Motif/Work)", "Category": "Work", "File": "4.csv"},
    {"Original": "Illustrations for De Bello Belgico", "Name": "Illustrations for De Bello Belgico", "Category": "Work", "File": "6.csv"},
    {"Original": "Joint caricature of Simonelli and Mola", "Name": "Joint Caricature of Simonelli and Mola", "Category": "Work", "File": "6.csv"},
    {"Original": "Minori Osservanti", "Name": "Order of Friars Minor (Observants)", "Category": "Organization", "File": "7.csv"},
    {"Original": "Statue of Field Marshal Schulenburg", "Name": "Statue of Field Marshal Schulenburg", "Category": "Work", "File": "8.csv"}
]

df_dupes = pd.DataFrame(duplicates_list)
print(df_dupes.to_string(index=False))
