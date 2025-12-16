import os
from docx import Document

def convert_docx_to_md(docx_path):
    if not os.path.exists(docx_path):
        print(f"File not found: {docx_path}")
        return

    print(f"Converting {docx_path}...")
    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"Error reading {docx_path}: {e}")
        return

    md_lines = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        style_name = para.style.name
        
        # Basic style mapping
        if style_name.startswith('Heading 1'):
            md_lines.append(f"# {text}")
        elif style_name.startswith('Heading 2'):
            md_lines.append(f"## {text}")
        elif style_name.startswith('Heading 3'):
            md_lines.append(f"### {text}")
        elif 'List' in style_name or style_name.startswith('List Paragraph'):
            md_lines.append(f"- {text}")
        else:
            md_lines.append(text)
            
        md_lines.append("") # Add newline after each paragraph

    # Construct output path
    base, _ = os.path.splitext(docx_path)
    md_path = base + ".md"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    
    print(f"Saved to {md_path}")

if __name__ == "__main__":
    base_dir = r"c:\Users\001\Desktop\Github-Project\PnPDataset\07-MML"
    files = ["Reademe-A.docx", "Readme-B.docx"]
    
    for filename in files:
        full_path = os.path.join(base_dir, filename)
        convert_docx_to_md(full_path)
