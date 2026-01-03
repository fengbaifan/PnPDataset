import pandas as pd
import os

# Define file paths
base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset\10-Worklist-index"
input_file = os.path.join(base_dir, "worklist-02.csv")
output_file = os.path.join(base_dir, "worklist-02_structured.csv")

# Read the CSV
df = pd.read_csv(input_file)

# Rename existing match columns to be Artist specific
# Assuming Matched_QID and Matched_Full_Name correspond to Artist
df.rename(columns={
    'Matched_QID': 'Artist_QID',
    'Matched_Full_Name': 'Artist_Full_Name'
}, inplace=True)

# Add empty columns for Title and Location QIDs if they don't exist
if 'Title_Description_QID' not in df.columns:
    df['Title_Description_QID'] = ""
if 'Location_QID' not in df.columns:
    df['Location_QID'] = ""

# Define the desired column order
# We want: ..., Artist, Artist_Full_Name, Artist_QID, Title_Description, Title_Description_QID, Location, Location_QID, ...
# We need to preserve other columns like Plate_ID, Sub_ID at the beginning.

desired_order = [
    'Plate_ID', 
    'Sub_ID', 
    'Artist', 
    'Artist_Full_Name', 
    'Artist_QID', 
    'Title_Description', 
    'Title_Description_QID', 
    'Location', 
    'Location_QID'
]

# If there are any other columns in the original df, append them at the end
existing_columns = df.columns.tolist()
for col in existing_columns:
    if col not in desired_order:
        desired_order.append(col)

# Reorder the dataframe
df = df[desired_order]

# Save the result
df.to_csv(output_file, index=False)

print(f"Successfully processed {input_file}")
print(f"Saved structured file to {output_file}")
print("Columns:", df.columns.tolist())
