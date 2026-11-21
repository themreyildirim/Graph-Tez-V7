"""WP07 kapanışı: hash, notebook ve ham dosyada yalnız stat kontrolü."""
from pathlib import Path
import hashlib
import json
import re
import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'reports/qa/WP07'


def main():
    checks = {}
    for name in ('prior_outputs_hashes.json','input_manifest.json'):
        manifest=json.loads((QA/name).read_text(encoding='utf-8'))
        bad=[p for p,h in manifest.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
        assert not bad,bad
        checks[name]={'checked':len(manifest),'changed':bad}
    required = [ROOT/f'reports/WP{i:02}.md' for i in range(7)]
    assert all(p.is_file() for p in required)
    checks['previous_WP_reports_present'] = 7
    sources=json.loads((ROOT/'reports/qa/WP06/aliases_manifest.json').read_text(encoding='utf-8'))
    sources+=json.loads((ROOT/'reports/qa/WP06/links_manifest.json').read_text(encoding='utf-8'))
    xml=json.loads((ROOT/'reports/qa/WP05/xml_extract_manifest.json').read_text(encoding='utf-8'))
    sources.append({'file':xml['source'],'size_bytes':xml['size_bytes'],'mtime_ns':xml['mtime_ns']})
    sider=json.loads((ROOT/'reports/qa/WP03/source_manifest.json').read_text(encoding='utf-8'))
    sources.append({'file':sider['sider_path'],'size_bytes':sider['source_size'],'mtime_ns':sider['source_mtime_ns']})
    for s in sources:
        stat=Path(s['file']).stat()
        assert stat.st_size==s['size_bytes'] and stat.st_mtime_ns==s['mtime_ns'],s['file']
    checks['raw_sources']={'unique_files_metadata_checked':len(set(s['file'] for s in sources)),
                           'content_rescanned':False,'hash_recomputed':False,
                           'limit':'Metadata eşitliği içerik hash doğrulamasının yerine geçmez; WP07 ham içerik açmaz.'}
    nb=nbformat.read(ROOT/'notebooks/WP07_data_integration.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outs=[o for c in code for o in c.outputs]
    assert len(code)==8 and [c.execution_count for c in code]==list(range(1,9))
    assert not any(o.output_type=='error' for o in outs)
    assert not any(o.output_type=='stream' and o.name=='stderr' for o in outs)
    assert sum('image/png' in o.get('data',{}) for o in outs)==6
    rows=[len(re.findall(r'<tr(?:\s[^>]*)?>',o.get('data',{}).get('text/html','')))-1 for o in outs]
    assert 62 in rows
    fig=ROOT/'reports/figures/WP07'
    assert len(list(fig.glob('*.png')))==6
    html=(fig/'drug_modality_interactive.html').read_text(encoding='utf-8')
    assert not re.search(r'<script[^>]+src\s*=',html,re.I)
    checks['notebook']={'executed_code_cells':8,'embedded_png':6,'full_drug_table_rows':62,'errors':0}
    checks['figures']={'png_visually_reviewed':6,'offline_html':1,'live_browser_tested':False}
    text=(QA/'test_results.txt').read_text(encoding='utf-8')
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',text)
    assert match and match.group(1)=='25' and text.rstrip().endswith('OK')
    checks['tests']={'passed':int(match.group(1)),'seconds':float(match.group(2))}
    missing=[]
    for relative, identity in [('reports/qa/WP04/chemical_features_clean.csv','id'),('reports/qa/WP05/protein_features.csv','accession')]:
        f=pd.read_csv(ROOT/relative)
        for column in f.columns:
            if column!=identity:
                count=int(f[column].isna().sum())
                missing.append({'source':relative,'field':column,'records':len(f),'missing':count,'missing_fraction':count/len(f)})
    pd.DataFrame(missing).to_csv(QA/'source_feature_missingness.csv',index=False,encoding='utf-8-sig')
    checks['scope']={'WP':'WP07','training':False,'WP08_started':False,'decisions_frozen':False}
    (QA/'artifact_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=True,indent=2))


if __name__=='__main__':main()
