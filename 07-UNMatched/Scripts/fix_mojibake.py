import pandas as pd

# Load the merged dataset
file_path = "merged_1_9.csv"
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

# Define mapping for mojibake correction
# Based on observed patterns:
# 迄 -> ù (Gesù)
# 辰 -> ò (Niccolò, Almorò)
# 谷 -> é (Estrées, Abbé)
# 豕 -> è (Vrillière, Griè?) - Wait, 'Gri豕' was 'Grill' in analysis? Let's check context.
# Actually 'Gri豕' -> 'Griè' or 'Grill'? 
# 'Angelica Gri豕' -> 'Angelica Grill' seems unlikely if it's mojibake. 
# Let's look at 'La Vrilli豕re' -> 'La Vrillière'. So 豕 -> è.
# 角 -> à (Città, Prà)
# 赤 -> í (María)
# 邦 -> ü (Kurfürst -> Kuf邦rst)
# “～ -> ò (Almor“～ -> Almorò)
# ＊ -> ' (Nell＊ingresso -> Nell'ingresso)
# ? -> ll (Prà de?a Va?e -> Prà della Valle) - This is a guess, need to be careful.
# 迄 -> ù
# 谷 -> é
# 豕 -> è
# 辰 -> ò
# 角 -> à
# 赤 -> í
# 邦 -> ü

replacements = {
    '迄': 'ù',
    '辰': 'ò',
    '谷': 'é',
    '豕': 'è',
    '角': 'à',
    '赤': 'í',
    '邦': 'ü',
    '“～': 'ò',
    '＊': "'",
    'O迄': 'Où', # Special case
}

def fix_text(text):
    if not isinstance(text, str):
        return text
    
    # Apply simple char replacements
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # Specific fixes for complex cases
    if 'Prà de?a Va?e' in text:
        text = text.replace('Prà de?a Va?e', 'Prà della Valle')
    
    return text

# Apply fixes to relevant columns
print("--- Applying Fixes ---")
df['Original_Entry'] = df['Original_Entry'].apply(fix_text)
df['Refined_Formal_Name'] = df['Refined_Formal_Name'].apply(fix_text)

# Verify fixes
# Check for remaining mojibake chars
mojibake_chars = ['迄', '谷', '豕', '辰', '邦', '角', '赤', '＊', '～']
def has_mojibake(text):
    if not isinstance(text, str):
        return False
    return any(char in text for char in mojibake_chars)

remaining_issues = df[df['Original_Entry'].apply(has_mojibake) | df['Refined_Formal_Name'].apply(has_mojibake)]
print(f"Remaining rows with potential issues: {len(remaining_issues)}")
if len(remaining_issues) > 0:
    print(remaining_issues[['Original_Entry', 'Refined_Formal_Name']].to_string())

# Save the fixed file
output_file = "merged_1_9_fixed.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\nFixed data saved to '{output_file}'")
