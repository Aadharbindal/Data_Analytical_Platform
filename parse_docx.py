import os
import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            # Namespace for Word
            word_ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for paragraph in tree.findall('.//w:p', word_ns):
                texts = [node.text for node in paragraph.findall('.//w:t', word_ns) if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error reading {docx_path}: {e}"

def main():
    directory = r'c:\Users\user\Documents\Data_Analytics'
    out_dir = os.path.join(directory, 'parsed_texts')
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in os.listdir(directory):
        if filename.endswith('.docx'):
            file_path = os.path.join(directory, filename)
            text = extract_text_from_docx(file_path)
            
            out_path = os.path.join(out_dir, filename.replace('.docx', '.txt'))
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Parsed: {filename}")

if __name__ == '__main__':
    main()
