import pandas as pd
import re
import os

file_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\08-Recheck\01-Merged_Recheck.csv"
try:
    df = pd.read_csv(file_path, encoding='utf-8-sig')
except:
    df = pd.read_csv(file_path, encoding='gbk')

def extract_tag(text):
    if pd.isna(text): return "No Note"
    match = re.search(r'\[(.*?)\]', str(text))
    return match.group(1) if match else "Other Note"

df['Note_Tag'] = df['Status/Notes'].apply(extract_tag)
other_notes = df[df['Note_Tag'] == "Other Note"]['Status/Notes'].head(10).tolist()
print("Examples of 'Other Note':")
for note in other_notes:
    print(f"- {note}")
