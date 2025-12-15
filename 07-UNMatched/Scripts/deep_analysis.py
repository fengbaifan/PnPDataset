import pandas as pd
import re

# Load the merged dataset
file_path = "merged_1_9.csv"
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

print(f"--- Dataset Overview ---")
print(f"Total Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

# 1. Category Analysis
print(f"\n--- Category Distribution ---")
category_counts = df['Refined_Category'].value_counts()
print(category_counts)

# 2. Name Complexity Analysis
# Check for names with parentheses (often indicating disambiguation or role)
df['Has_Parentheses'] = df['Refined_Formal_Name'].astype(str).str.contains(r'\(.*\)')
parentheses_count = df['Has_Parentheses'].sum()
print(f"\nEntries with Parentheses in Formal Name: {parentheses_count} ({parentheses_count/len(df)*100:.1f}%)")

# Check for names with slashes (often indicating multiple entities or complex types)
df['Has_Slash'] = df['Refined_Formal_Name'].astype(str).str.contains('/')
slash_count = df['Has_Slash'].sum()
print(f"Entries with Slashes in Formal Name: {slash_count}")

# 3. Status/Notes Tag Analysis
print(f"\n--- Status/Notes Tag Analysis ---")
# Extract all tags like [Tag Name]
tags = df['Status/Notes'].astype(str).str.extractall(r'(\[[^\]]+\])')[0].value_counts()
print(tags.head(10))

# 4. Potential Encoding Issues Detection
# Look for common mojibake characters or sequences
# Common indicators: 迄, 谷, 豕, 辰, 邦, 角, 赤, 
mojibake_chars = ['迄', '谷', '豕', '辰', '邦', '角', '赤', '＊', '～']
def has_mojibake(text):
    if not isinstance(text, str):
        return False
    return any(char in text for char in mojibake_chars)

df['Potential_Mojibake'] = df['Original_Entry'].apply(has_mojibake) | df['Refined_Formal_Name'].apply(has_mojibake)
mojibake_count = df['Potential_Mojibake'].sum()
print(f"\n--- Potential Encoding Issues ---")
print(f"Rows with potential mojibake: {mojibake_count}")
if mojibake_count > 0:
    print(df[df['Potential_Mojibake']][['Original_Entry', 'Refined_Formal_Name']].head(10).to_string())

# 5. Entity Type Specific Analysis
print(f"\n--- Person Analysis ---")
persons = df[df['Refined_Category'] == 'Person']
print(f"Total Persons: {len(persons)}")
# Check for single names (potential mononyms or incomplete data)
single_names = persons[~persons['Refined_Formal_Name'].str.contains(' ', na=False)]
print(f"Single-word Person names: {len(single_names)}")
if len(single_names) > 0:
    print(single_names['Refined_Formal_Name'].head(5).tolist())

print(f"\n--- Work Analysis ---")
works = df[df['Refined_Category'].str.contains('Work', na=False)]
print(f"Total Works (including subtypes): {len(works)}")
