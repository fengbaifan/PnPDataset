import pandas as pd

file_path = "merged_1_9_final.csv"
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

print(f"--- Final Validation: {file_path} ---")
print(f"Total Rows: {len(df)}")

# 1. Check for Duplicates
duplicates = df[df.duplicated(subset=['Original_Entry', 'Refined_Formal_Name', 'Refined_Category'], keep=False)]
print(f"Duplicates found: {len(duplicates)}")

# 2. Check for Mojibake
mojibake_chars = ['迄', '谷', '豕', '辰', '邦', '角', '赤', '＊', '～']
def has_mojibake(text):
    if not isinstance(text, str):
        return False
    return any(char in text for char in mojibake_chars)

mojibake_count = df['Original_Entry'].apply(has_mojibake).sum() + df['Refined_Formal_Name'].apply(has_mojibake).sum()
print(f"Mojibake entries found: {mojibake_count}")

# 3. Verify Splits
# Check if 'Robert Boyle' exists (result of split)
boyle = df[df['Refined_Formal_Name'] == 'Robert Boyle']
print(f"Split verification (Robert Boyle exists): {not boyle.empty}")

# 4. Verify Deduplication
# Check count of 'Altar of Friendship'
altar = df[df['Original_Entry'] == 'Altar of Friendship']
print(f"Deduplication verification (Altar of Friendship count): {len(altar)}")

# 5. Check for Nulls
print("\nNull Values:")
print(df.isnull().sum())
