import pandas as pd
import os

# Configuration
input_dir = r'c:\Users\001\Desktop\14-Relation\03-Handmade'

def convert_to_csv():
    print(f"Scanning directory: {input_dir}")
    if not os.path.exists(input_dir):
        print(f"Directory not found: {input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
    
    if not files:
        print("No .xlsx files found.")
        return

    print(f"Found {len(files)} files: {files}")

    for file in files:
        file_path = os.path.join(input_dir, file)
        output_path = os.path.join(input_dir, file.replace('.xlsx', '.csv'))
        
        print(f"Converting {file} to CSV...")
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Save as CSV
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"Saved: {output_path}")
            
        except Exception as e:
            print(f"Error converting {file}: {e}")

if __name__ == "__main__":
    convert_to_csv()
