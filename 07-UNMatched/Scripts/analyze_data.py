import pandas as pd
import os

files = [f"{i}.csv" for i in range(1, 10)]
dfs = []

print("--- Loading Files ---")
for file in files:
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            df['Source_File'] = file
            dfs.append(df)
            print(f"Loaded {file}: {len(df)} rows")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    else:
        print(f"File not found: {file}")

if not dfs:
    print("No data loaded.")
    exit()

all_data = pd.concat(dfs, ignore_index=True)

print("\n--- General Info ---")
print(f"Total rows: {len(all_data)}")
print(f"Columns: {list(all_data.columns)}")

print("\n--- Missing Values ---")
print(all_data.isnull().sum())

print("\n--- Duplicates ---")
# Check for duplicates in Original_Entry
duplicates = all_data[all_data.duplicated(subset=['Original_Entry'], keep=False)]
print(f"Duplicate Original_Entry count: {len(duplicates)}")
if len(duplicates) > 0:
    print(duplicates[['Original_Entry', 'Source_File']].sort_values('Original_Entry').head(10))

print("\n--- Category Distribution ---")
if 'Refined_Category' in all_data.columns:
    print(all_data['Refined_Category'].value_counts())
else:
    print("Column 'Refined_Category' not found.")

print("\n--- Status/Notes Analysis ---")
if 'Status/Notes' in all_data.columns:
    # Extract tags like [Category Fix]
    # We convert to string first to handle potential NaN values gracefully
    tags = all_data['Status/Notes'].astype(str).str.extractall(r'(\[[^\]]+\])')[0].value_counts()
    print(tags)
else:
    print("Column 'Status/Notes' not found.")

print("\n--- Sample Data Issues ---")
if 'Refined_Formal_Name' in all_data.columns:
    # Check for potential whitespace issues
    # Ensure column is string type
    all_data['Refined_Formal_Name'] = all_data['Refined_Formal_Name'].astype(str)
    whitespace_issues = all_data[all_data['Refined_Formal_Name'].str.strip() != all_data['Refined_Formal_Name']]
    print(f"Rows with leading/trailing whitespace in Refined_Formal_Name: {len(whitespace_issues)}")
    if len(whitespace_issues) > 0:
        print(whitespace_issues[['Refined_Formal_Name', 'Source_File']].head())
