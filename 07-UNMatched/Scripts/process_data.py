import pandas as pd

# Load the fixed dataset
file_path = "merged_1_9_fixed.csv"
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

print(f"Initial rows: {len(df)}")

# --- Step 1: Handle Split Required Items ---
print("\n--- Processing Splits ---")

# Define split logic
# Format: Original_Entry substring : [ (New_Name, New_Category), ... ]
split_map = {
    "Chiari, Giuseppe and Tommaso": [
        ("Giuseppe Chiari", "Person"),
        ("Tommaso Chiari", "Person")
    ],
    "Cortese, Giacomo and Guglielmo": [
        ("Giacomo Cortese", "Person"),
        ("Guglielmo Cortese", "Person")
    ],
    "Courtois, Jacques and Guillaume": [
        ("Jacques Courtois", "Person"),
        ("Guillaume Courtois", "Person")
    ],
    "Rossi, Ventura and Lorenzo": [
        ("Ventura Rossi", "Person"),
        ("Lorenzo Rossi", "Person")
    ],
    "Valeriani, Domenico and Giuseppe": [
        ("Domenico Valeriani", "Person"),
        ("Giuseppe Valeriani", "Person")
    ],
    "Boyle/Locke/Sydenham": [
        ("Robert Boyle", "Person"),
        ("John Locke", "Person"),
        ("Thomas Sydenham", "Person")
    ],
    "Viterbo Moroni": [
        ("Viterbo", "Place"),
        ("Giovanni Battista Moroni", "Person")
    ]
}

new_rows = []
indices_to_drop = []

for index, row in df.iterrows():
    status = str(row['Status/Notes'])
    original = str(row['Original_Entry'])
    
    if "[Split Required]" in status:
        # Find matching split logic
        matched = False
        for key, splits in split_map.items():
            if key in original:
                print(f"Splitting: {original}")
                for new_name, new_cat in splits:
                    new_row = row.copy()
                    new_row['Refined_Formal_Name'] = new_name
                    new_row['Refined_Category'] = new_cat
                    new_row['Status/Notes'] = "[Split] Derived from: " + original
                    new_rows.append(new_row)
                indices_to_drop.append(index)
                matched = True
                break
        
        if not matched:
            print(f"Warning: No split logic defined for: {original}")

# Remove original rows and add new ones
if indices_to_drop:
    df = df.drop(indices_to_drop)
    df_new = pd.DataFrame(new_rows)
    df = pd.concat([df, df_new], ignore_index=True)
    print(f"Rows after splitting: {len(df)}")

# --- Step 2: Remove Duplicates ---
print("\n--- Removing Duplicates ---")
# We consider a duplicate if Original_Entry, Refined_Formal_Name, and Refined_Category are identical
# We keep the first occurrence
before_dedup = len(df)
df = df.drop_duplicates(subset=['Original_Entry', 'Refined_Formal_Name', 'Refined_Category'], keep='first')
after_dedup = len(df)
print(f"Removed {before_dedup - after_dedup} duplicates.")
print(f"Final rows: {len(df)}")

# Save final file
output_file = "merged_1_9_final.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\nFinal processed data saved to '{output_file}'")
