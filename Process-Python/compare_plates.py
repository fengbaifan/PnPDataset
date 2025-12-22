# Worklist_Plates 与 00_05_List_of_Plates.md 数据比对脚本

import csv
import re

# 读取 Worklist_Plates.csv
worklist_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\10-Worklist-index\Worklist_Plates.csv"
worklist_plates = []
with open(worklist_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        plate_id = row['Plate_ID']
        sub_id = row['Sub_ID']
        artist = row['Artist']
        title = row['Title_Description']
        worklist_plates.append({
            'plate_id': plate_id,
            'sub_id': sub_id,
            'artist': artist,
            'title': title
        })

# 读取 00_05_List_of_Plates.md
md_path = r"c:\Users\001\Desktop\Github-Project\PnPDataset\02-Markdown\00_05_List_of_Plates.md"
md_plates = []
plate_pattern = re.compile(r'^(\d+)([a-z]?)\s*[:.]?\s*(.*?)(?:\(|\{|$)', re.IGNORECASE)
with open(md_path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        match = plate_pattern.match(line)
        if match:
            plate_id, sub_id, rest = match.groups()
            # 提取艺术家和标题
            if ':' in rest:
                artist, title = rest.split(':', 1)
                artist = artist.strip()
                title = title.strip()
            else:
                artist = ''
                title = rest.strip()
            md_plates.append({
                'plate_id': plate_id,
                'sub_id': sub_id,
                'artist': artist,
                'title': title
            })

# 比对完整性
worklist_set = set((p['plate_id'], p['sub_id'], p['artist'], p['title']) for p in worklist_plates)
md_set = set((p['plate_id'], p['sub_id'], p['artist'], p['title']) for p in md_plates)

only_in_worklist = worklist_set - md_set
only_in_md = md_set - worklist_set

print('仅在 Worklist_Plates.csv 中的条目:')
for item in only_in_worklist:
    print(item)
print('\n仅在 00_05_List_of_Plates.md 中的条目:')
for item in only_in_md:
    print(item)
