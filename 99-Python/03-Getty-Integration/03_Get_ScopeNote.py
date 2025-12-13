def get_scopenote():
    ulan_file = r'c:\Users\001\Desktop\Github-Project\PnPDataset\Getty\The Union List of Artist Names (ULAN)\ULANOut_Full.nt'
    target_note_id = '<http://vocab.getty.edu/ulan/scopeNote/31502>'
    
    print(f"Scanning for scope note: {target_note_id}...")
    
    try:
        with open(ulan_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith(target_note_id):
                    print(line.strip())
    except FileNotFoundError:
        print("File not found.")

if __name__ == "__main__":
    get_scopenote()
