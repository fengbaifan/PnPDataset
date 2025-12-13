import os

def get_hogarth_details():
    ulan_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\Getty\The Union List of Artist Names (ULAN)\ULANOut_Full.nt'
    output_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\99-Python\02-Analysis\Hogarth_Details.txt'
    
    target_ids = {
        '500004242', 
        '500006820', 
        '500377518'
    }
    
    print(f"Scanning {ulan_file} for details on IDs: {target_ids}...")
    
    found_lines = []
    
    try:
        with open(ulan_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Check if the line starts with one of our target IDs
                # The format is <http://vocab.getty.edu/ulan/ID>
                for tid in target_ids:
                    if line.startswith(f'<http://vocab.getty.edu/ulan/{tid}>'):
                        found_lines.append(line.strip())
                        break
                        
    except FileNotFoundError:
        print(f"Error: ULAN file not found at {ulan_file}")
        return

    print(f"Found {len(found_lines)} triples.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Detailed ULAN Data for Hogarth, William Candidates\n")
        f.write("==================================================\n\n")
        
        # Group by ID for better readability
        grouped = {tid: [] for tid in target_ids}
        for line in found_lines:
            for tid in target_ids:
                if tid in line:
                    grouped[tid].append(line)
                    break
        
        for tid, lines in grouped.items():
            f.write(f"ID: {tid}\n")
            f.write("-" * 20 + "\n")
            for l in lines:
                f.write(f"{l}\n")
            f.write("\n")

    print(f"Details saved to {output_file}")

if __name__ == "__main__":
    get_hogarth_details()
