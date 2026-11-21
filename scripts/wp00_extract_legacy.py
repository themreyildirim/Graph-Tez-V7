"""Tarihsel belgeleri yalnız metin olarak oku; kod/notebook çalıştırılmaz."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/qa/legacy_text'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in sorted((ROOT / 'legacy').iterdir()):
        if not path.is_file():
            continue
        units = []
        if path.suffix == '.pdf':
            reader = PdfReader(path)
            units = [f'--- PDF sayfa {i} ---\n{p.extract_text()}' for i, p in enumerate(reader.pages, 1)]
        elif path.suffix == '.docx':
            with ZipFile(path) as z:
                doc = ET.fromstring(z.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            # Paragraf sırası, tablolar dahil.
            units = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in doc.findall('.//w:p', ns)]
        elif path.suffix == '.ipynb':
            notebook = json.loads(path.read_text(encoding='utf-8'))
            units = [f'--- Hücre {i}: {c["cell_type"]} ---\n' + ''.join(c.get('source', []))
                     for i, c in enumerate(notebook['cells'], 1)]
        elif path.suffix in {'.md', '.py'}:
            units = [path.read_text(encoding='utf-8')]
        else:
            continue
        text = '\n\n'.join(units)
        dest = OUT / (path.name + '.txt')
        dest.write_text(text, encoding='utf-8')
        manifest.append({'file': path.name, 'units': len(units), 'characters': len(text),
                         'method': 'text extraction only; no execution; no visual layout validation'})
    (OUT.parent / 'legacy_review_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
