"""WP08 ilk deney fazı kapanışı: mevcut testler ve salt okunur bütünlük denetimi.

Deney komutlarını, B0 tahminini veya eski artefakt yazıcılarını çalıştırmaz.
Mevcut LR unit testleri yalnız RAM'de küçük fit/reprodüksiyon kontrolleri yapar.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT/'reports/qa/WP08/final_closure_v1'
PREP = ROOT/'reports/qa/WP08/experimental_preparation'
B0 = ROOT/'reports/qa/WP08/B0_frequency_reference_v1'
BASE = ROOT/'reports/qa/WP08/baseline_v1'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def csv(path, frame):
    frame.to_csv(path, index=False, encoding='utf-8-sig', lineterminator='\n')


def snapshot():
    QA.mkdir(parents=True, exist_ok=True)
    path = QA/'accepted_artifacts_sha256.json'
    if path.exists():
        raise RuntimeError('Closure snapshot already exists; do not redefine accepted inputs')
    manifest = {}
    for folder in ('docs','scripts','tests','configs','reports','notebooks','models'):
        for source in sorted((ROOT/folder).rglob('*')):
            if not source.is_file() or '__pycache__' in source.parts:
                continue
            rel = source.relative_to(ROOT).as_posix()
            if ('final_closure_v1' in source.parts or source.name.startswith(('wp08_final_', 'test_wp08_final_',
                'WP08_FINAL_CONCLUSIONS', 'WP08_final_conclusions', 'WP09_COMPARISON_CONTRACT'))):
                continue
            manifest[rel] = sha(source)
    write_json(path, manifest)
    print(f'Frozen closure preservation snapshot: {len(manifest)} files', flush=True)


def preservation():
    manifest = json.loads((QA/'accepted_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad = [p for p,h in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p) != h]
    if bad:
        raise AssertionError(f'Accepted artifacts changed: {bad}')
    return {'files_checked':len(manifest), 'changed':bad}


def run_tests():
    preservation()
    rows = []
    environment = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    for suite in ('test_wp08.py','test_wp08_prepare.py','test_wp08_baseline.py','test_wp08_b0.py'):
        started = time.perf_counter()
        result = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',suite,'-v'],
            cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf-8', errors='replace')
        text = result.stdout + result.stderr
        (QA/(suite.removesuffix('.py')+'_rerun.txt')).write_text(text, encoding='utf-8')
        match = re.search(r'Ran (\d+) tests in ([\d.]+)s', text)
        row = {'suite':suite,'tests':int(match.group(1)) if match else 0,
            'unittest_seconds':float(match.group(2)) if match else None,
            'wall_seconds':time.perf_counter()-started,'exit_code':result.returncode,
            'passed':result.returncode == 0 and text.rstrip().endswith('OK'),
            'log':suite.removesuffix('.py')+'_rerun.txt',
            'persistent_model_or_score_writes':False,
            'in_memory_fit_checks':'baseline unit tests include fixed tiny reproducibility/mutation fits; no new experiment'}
        rows.append(row)
        csv(QA/'existing_test_suite_results.csv', pd.DataFrame(rows))
        print(f'{suite}: {row["tests"]} tests, passed={row["passed"]}', flush=True)
        if not row['passed']:
            raise RuntimeError(f'Existing test suite failed: {suite}; see new closure log')
    preservation()


def audit():
    checks = {'accepted_artifacts':preservation()}
    manifest_paths = [
        ROOT/'reports/qa/WP08/prior_outputs_hashes.json', ROOT/'reports/qa/WP08/input_manifest.json',
        PREP/'prior_outputs_hashes.json', PREP/'input_manifest.json',
        BASE/'prior_outputs_hashes.json', BASE/'preparation_input_manifest.json', BASE/'model_artifact_manifest.json',
        B0/'prior_outputs_hashes.json', B0/'input_manifest.json']
    checks['historical_manifests'] = []
    for path in manifest_paths:
        manifest = json.loads(path.read_text(encoding='utf-8'))
        bad = [p for p,h in manifest.items() if sha(ROOT/p) != h]
        assert not bad, (str(path),bad)
        checks['historical_manifests'].append({'path':path.relative_to(ROOT).as_posix(),'entries':len(manifest),'changed':bad})
    frozen = json.loads((PREP/'frozen_split_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(PREP/p)==h for p,h in frozen.items())
    checks['frozen_split_manifest'] = frozen
    checks['specification_sha256'] = json.loads((PREP/'split_lock_v1.json').read_text(encoding='utf-8'))['specification_sha256']
    checks['seed'] = 20261106
    sources = json.loads((ROOT/'reports/qa/WP06/aliases_manifest.json').read_text(encoding='utf-8'))
    sources += json.loads((ROOT/'reports/qa/WP06/links_manifest.json').read_text(encoding='utf-8'))
    xml = json.loads((ROOT/'reports/qa/WP05/xml_extract_manifest.json').read_text(encoding='utf-8'))
    sider = json.loads((ROOT/'reports/qa/WP03/source_manifest.json').read_text(encoding='utf-8'))
    sources += [{'file':xml['source'],'size_bytes':xml['size_bytes'],'mtime_ns':xml['mtime_ns']},
        {'file':sider['sider_path'],'size_bytes':sider['source_size'],'mtime_ns':sider['source_mtime_ns']}]
    metadata = []
    for source in sources:
        try:
            stat = Path(source['file']).stat()
            same = stat.st_size==source['size_bytes'] and stat.st_mtime_ns==source['mtime_ns']
            metadata.append({'file':source['file'],'exists':True,'same_size_and_mtime':same})
        except OSError as exc:
            metadata.append({'file':source['file'],'exists':False,'same_size_and_mtime':False,'error':str(exc)})
    checks['raw_metadata_only'] = metadata
    checks['raw_content_rescan_or_hash'] = False
    csv(QA/'raw_source_metadata_check.csv',pd.DataFrame(metadata))
    # Kaynak PT uzayı bağımsız küçük QA kontrolü; ham SIDER yeniden okunmaz.
    source = pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv')
    source = source[source.conservative]
    assert not source.duplicated(['id','meddra_cui']).any()
    checks['source_PT'] = {'drugs':source.id.nunique(),'PT_CUI':source.meddra_cui.nunique(),'positive_pairs':len(source)}
    assert checks['source_PT'] == {'drugs':62,'PT_CUI':1061,'positive_pairs':6416}
    checks['old_models'] = {'version':json.loads((BASE/'run_config.json').read_text(encoding='utf-8'))['version'],
        'parameter_npz':len(list((ROOT/'models/WP08_baseline_v1').glob('*.npz'))),
        'metadata_json':len(list((ROOT/'models/WP08_baseline_v1').glob('*.json'))),
        'selected_C_sha256':sha(BASE/'selected_C.csv'), 'OOF_sha256':sha(BASE/'oof_predictions.csv')}
    checks['B0'] = {'version':'B0_frequency_reference_v1','policy_sha256':sha(B0/'policy_before_B0_results.json'),
        'frequency_sha256':sha(B0/'train_frequency_estimates.csv'),'query_score_sha256':sha(B0/'B0_outer_query_scores.csv')}
    checks['WP08_phase1_closed_by_user_scope_decision'] = True
    checks['WP09_training_authorized'] = False
    checks['new_experiment_or_hyperparameter_search'] = False
    write_json(QA/'integrity_audit.json',checks)
    # Topolojik ön kontrol: mevcut küçük WP06 kenar tablosu, yalnız train bağlı proteinler.
    parts = pd.read_csv(PREP/'nested_partitions_v1.csv')
    relations = pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv')
    mapping = pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv')
    strict = mapping[mapping.strict_taxon_match & mapping.network_taxid.eq(9606)]
    edges = pd.read_csv(ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv')
    assert len(strict)==63 and edges.network_taxid.eq(9606).all()
    rows=[]
    for context,sub in parts.groupby('context'):
        train=set(sub[sub.split.eq('train')].drug_id)
        proteins=set(relations[relations.drug_id.isin(train)&relations.sequence_available].accession)
        nodes=set(strict[strict.accession.isin(proteins)].string_id)
        for threshold in (400,700,900):
            e=edges[edges.protein1.isin(nodes)&edges.protein2.isin(nodes)&edges.combined_score.ge(threshold)&~edges.score_conflict]
            incident=set(e.protein1)|set(e.protein2)
            rows.append({'context':context,'protocol':sub.iloc[0].protocol,'outer_fold':int(sub.iloc[0].outer_fold),
                'inner_fold':int(sub.iloc[0].inner_fold),'train_drugs':len(train),'train_linked_sequence_proteins':len(proteins),
                'strict_human_train_nodes':len(nodes),'threshold':threshold,'undirected_PPI_pairs':len(e),
                'incident_human_nodes':len(incident),'isolated_human_nodes':len(nodes-incident),
                'scope':'planning preflight only; no graph object or model; threshold not selected'})
    csv(QA/'WP09_train_only_topology_preflight.csv',pd.DataFrame(rows))
    print(f'Integrity passed: {checks["accepted_artifacts"]["files_checked"]} accepted files; 1061 PT; raw metadata only',flush=True)


def final_artifact_check():
    import nbformat
    checks={'preservation':preservation()}
    snapshot=json.loads((QA/'accepted_artifacts_sha256.json').read_text(encoding='utf-8'))
    before_models={p for p in snapshot if p.startswith('models/')}
    after_models={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    assert before_models==after_models, 'Model directory membership changed'
    checks['unchanged_model_file_membership']=len(before_models)
    contract=json.loads((QA/'WP09_comparison_contract_draft.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in contract['reference_files_sha256'].items())
    checks['comparison_contract_references']=len(contract['reference_files_sha256'])
    results=pd.read_csv(QA/'existing_test_suite_results.csv')
    assert results.passed.all() and results.tests.sum()==103
    extra=(QA/'closure_contract_test_results.txt').read_text(encoding='utf-8-sig')
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',extra)
    assert match and match.group(1)=='8' and extra.rstrip().endswith('OK')
    checks['tests']={'existing':103,'closure_contract_not_encoder':8,'total':111,
        'closure_test_seconds':float(match.group(2))}
    notebook=ROOT/'notebooks/WP08_final_conclusions.ipynb'
    nb=nbformat.read(notebook,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    outputs=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,7))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==3
    figures=sorted((ROOT/'reports/figures/WP08/final_closure_v1').glob('*.png'))
    assert len(figures)==3
    checks['notebook']={'executed_code_cells':6,'embedded_PNG':3,'error_or_stderr':False,'sha256':sha(notebook)}
    checks['figures']={'PNG_count':3,'visual_review':'All three viewed with view_image; labels and values readable',
        'new_HTML':False,'reason':'Static closure summary; prior offline interactive B0 notebook remains unchanged'}
    report=ROOT/'reports/WP08_FINAL_CONCLUSIONS.md'
    assert report.is_file() and (ROOT/'docs/plan/WP09_COMPARISON_CONTRACT_DRAFT.md').is_file()
    checks['scope']={'WP08_phase1_closed':True,'deferred_variants_completed':False,
        'WP09_implementation_or_training_started':False,'new_experiment_or_tuning':False,
        'RAM_unit_test_fits_only':True,'observed_record_proxy_not_clinical_risk':True}
    new_code=list((ROOT/'scripts').glob('wp08_final_*.py'))+[ROOT/'tests/test_wp08_final_review.py']
    checks['new_code_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(new_code)}
    checks['final_report_sha256']=sha(report)
    checks['draft_contract_markdown_sha256']=sha(ROOT/'docs/plan/WP09_COMPARISON_CONTRACT_DRAFT.md')
    write_json(QA/'artifact_validation.json',checks)
    print(f'Final artifacts verified; {checks["preservation"]["files_checked"]} files preserved; 103+8 tests passed; WP09 not started')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['snapshot','test','audit','preservation','finalize'])
    action=parser.parse_args().action
    if action=='snapshot':snapshot()
    elif action=='test':run_tests()
    elif action=='audit':audit()
    elif action=='finalize':final_artifact_check()
    else:print(json.dumps(preservation()))
