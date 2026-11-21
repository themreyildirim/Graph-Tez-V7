"""WP06 kapanış kontrolü: küçük çıktılar ve kaynak metadata; büyük dosya okuma yok."""
from pathlib import Path
import hashlib
import json
import re
import nbformat

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'reports/qa/WP06'


def main():
    checks = {}
    for filename in ('prior_outputs_hashes.json', 'input_manifest.json'):
        expected = json.loads((QA / filename).read_text(encoding='utf-8'))
        changed = [p for p, digest in expected.items()
                   if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
        assert not changed, changed
        checks[filename] = {'checked': len(expected), 'changed': changed}

    nb = nbformat.read(ROOT / 'notebooks/WP06_string_ppi_exploration.ipynb', as_version=4)
    nbformat.validate(nb)
    code = [c for c in nb.cells if c.cell_type == 'code']
    assert len(code) == 10 and all(c.execution_count is not None for c in code)
    outputs = [o for c in code for o in c.outputs]
    assert not any(o.output_type == 'error' for o in outputs)
    stderr = [o.text for o in outputs if o.output_type == 'stream' and o.name == 'stderr']
    assert not stderr, stderr
    embedded = sum('image/png' in o.get('data', {}) for o in outputs)
    html_tables = [o.get('data', {}).get('text/html', '') for o in outputs]
    row_counts = [len(re.findall(r'<tr(?:\s[^>]*)?>', t)) - 1
                  for t in html_tables if '<table' in t]
    assert embedded == 9 and 141 in row_counts and 62 in row_counts, row_counts
    checks['notebook'] = {'executed_code_cells': len(code), 'embedded_png': embedded,
                          'full_mapping_rows': 141, 'full_drug_rows': 62, 'errors': 0}
    figures = ROOT / 'reports/figures/WP06'
    png = sorted(p.name for p in figures.glob('*.png'))
    html = sorted(p.name for p in figures.glob('*.html'))
    assert len(png) == 9 and len(html) == 2
    for name in html:
        content = (figures / name).read_text(encoding='utf-8')
        assert not re.search(r'<script[^>]+src\s*=', content, re.I)
        assert 'combined_score' in content and 'STRING' in content
    checks['figures'] = {'png': png, 'offline_html': html,
                         'visual_png_review': 'all nine inspected',
                         'live_browser_interaction_tested': False}
    sources = json.loads((QA / 'aliases_manifest.json').read_text(encoding='utf-8'))
    sources += json.loads((QA / 'links_manifest.json').read_text(encoding='utf-8'))
    for source in sources:
        stat = Path(source['file']).stat()
        assert stat.st_size == source['size_bytes']
        assert stat.st_mtime_ns == source['mtime_ns']
    checks['raw_sources'] = {'metadata_records_checked': len(sources),
                             'large_files_rescanned_for_closure': False}
    report = (ROOT / 'reports/WP06.md').read_text(encoding='utf-8')
    test_log = (QA / 'test_results.txt').read_text(encoding='utf-8-sig')
    match = re.search(r'Ran (\d+) tests in ([\d.]+)s', test_log)
    assert match and match.group(1) == '23' and test_log.rstrip().endswith('OK')
    assert '23/23' in report and 'WP07' in report
    assert match.group(2).replace('.', ',') in report
    assert 'AWAITING_USER_APPROVAL' in (ROOT / 'run_status.md').read_text(encoding='utf-8')
    checks['status'] = 'WP06 complete; awaiting user approval; WP07 not started'
    (QA / 'artifact_validation.json').write_text(
        json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(checks, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
