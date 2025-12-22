# 深度分析 Worklist_Plates 与 00_05_List_of_Plates.md 的作品抽取完整度

import csv
import re
from collections import defaultdict

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

# 统计每个 plate_id 的作品数量
worklist_count = defaultdict(int)
for p in worklist_plates:
    key = (p['plate_id'], p['sub_id'])
    worklist_count[key] += 1
md_count = defaultdict(int)
for p in md_plates:
    key = (p['plate_id'], p['sub_id'])
    md_count[key] += 1

# 检查每个 plate_id/sub_id 的完整性
all_keys = set(worklist_count.keys()) | set(md_count.keys())
report = []
for key in sorted(all_keys):
    w = worklist_count.get(key, 0)
    m = md_count.get(key, 0)
    if w != m:
        report.append(f"Plate {key}: worklist={w}, md={m}")

# 检查作品内容差异
worklist_set = set((p['plate_id'], p['sub_id'], p['artist'], p['title']) for p in worklist_plates)
md_set = set((p['plate_id'], p['sub_id'], p['artist'], p['title']) for p in md_plates)
only_in_worklist = worklist_set - md_set
only_in_md = md_set - worklist_set

with open(r"c:\Users\001\Desktop\Github-Project\PnPDataset\Process-Python\plates_compare_report.txt", "w", encoding="utf-8") as f:
    f.write("=== Plate 数量不一致 ===\n")
    for line in report:
        f.write(line + "\n")
    f.write("\n=== 仅在 Worklist_Plates.csv 中的条目 ===\n")
    for item in only_in_worklist:
        f.write(str(item) + "\n")
    f.write("\n=== 仅在 00_05_List_of_Plates.md 中的条目 ===\n")
    for item in only_in_md:
        f.write(str(item) + "\n")

print("分析完成，详细报告已生成：plates_compare_report.txt")
