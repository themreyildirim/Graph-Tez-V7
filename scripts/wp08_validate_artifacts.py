"""WP08 protokol incelemesi kapanışı; ham kaynakta yalnız stat."""
from pathlib import Path
import json,hashlib,re
import nbformat

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08'


def main():
    checks={}
    for name in ('prior_outputs_hashes.json','input_manifest.json'):
        m=json.loads((QA/name).read_text(encoding='utf-8'))
        bad=[p for p,h in m.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
        assert not bad,bad;checks[name]={'count':len(m),'changed':bad}
    assert all((ROOT/f'reports/WP{i:02}.md').is_file() for i in range(8))
    nb=nbformat.read(ROOT/'notebooks/WP08_prediction_protocol.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,10))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==7
    counts=[len(re.findall(r'<tr(?:\s[^>]*)?>',o.get('data',{}).get('text/html','')))-1 for o in outputs]
    assert 62 in counts
    fig=ROOT/'reports/figures/WP08';assert len(list(fig.glob('*.png')))==7
    html=(fig/'structure_similarity_interactive.html').read_text(encoding='utf-8')
    assert not re.search(r'<script[^>]+src\s*=',html,re.I)
    text=(QA/'test_results.txt').read_text(encoding='utf-8');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',text)
    assert m and m.group(1)=='28' and text.rstrip().endswith('OK')
    checks['tests']={'passed':28,'seconds':float(m.group(2)),
                     'dependency_deprecation_warning':'torch.jit.script' in text}
    sources=json.loads((ROOT/'reports/qa/WP06/aliases_manifest.json').read_text(encoding='utf-8'))
    sources+=json.loads((ROOT/'reports/qa/WP06/links_manifest.json').read_text(encoding='utf-8'))
    xml=json.loads((ROOT/'reports/qa/WP05/xml_extract_manifest.json').read_text(encoding='utf-8'))
    sider=json.loads((ROOT/'reports/qa/WP03/source_manifest.json').read_text(encoding='utf-8'))
    sources += [{'file':xml['source'],'size_bytes':xml['size_bytes'],'mtime_ns':xml['mtime_ns']},
                {'file':sider['sider_path'],'size_bytes':sider['source_size'],'mtime_ns':sider['source_mtime_ns']}]
    for s in sources:
        stat=Path(s['file']).stat();assert stat.st_size==s['size_bytes'] and stat.st_mtime_ns==s['mtime_ns']
    checks['raw_metadata']={'unique_files':len(set(s['file'] for s in sources)),
                            'same_size_and_mtime':True,'content_rescan':False,'content_hash_revalidation':False}
    checks['notebook']={'executed_cells':9,'embedded_png':7,'full_62_drug_table':True,'errors':0}
    checks['figures']={'png_visual_review':7,'offline_html':1,'live_browser_tested':False}
    checks['scope']={'cohort':62,'model_training':False,'real_split':False,'real_preprocessor_fit':False,
                     'synthetic_preprocessor_tests':True,'graph_boundary_tests_only':True,
                     'methodology_approved':False,'WP09_started':False}
    (QA/'artifact_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=True,indent=2))


if __name__=='__main__':main()
