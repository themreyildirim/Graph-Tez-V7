"""WP09 son doğrulama: eski kaynaklar, yürütülmüş notebook, veri/encoder QA; eğitim yok."""
import json,re,sys,platform
import importlib.metadata
import numpy as np
import pandas as pd
import nbformat
from wp09_data import ROOT,QA,preserve,sha,json_write,validate_bundle


def main():
    checks={'prior_files_unchanged':preserve()}
    for name in ('input_manifest.json','prepared_artifact_manifest.json','shuffled_artifact_manifest.json'):
        paths=json.loads((QA/name).read_text(encoding='utf-8'))
        bad=[p for p,h in paths.items() if sha(ROOT/p)!=h]
        assert not bad,(name,bad)
        checks[name]={'count':len(paths),'changed':bad}
    protected=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    expected={p for p in protected if p.startswith('models/')}
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    assert actual==expected
    checks['no_model_directory_additions_or_changes']=True
    parts=pd.read_csv(ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv')
    for context,sub in parts.groupby('context'):
        with np.load(QA/'folds'/(context+'_train.npz'),allow_pickle=False) as a:graph={k:a[k] for k in a.files}
        with np.load(QA/'folds'/(context+'_query.npz'),allow_pickle=False) as a:query={k:a[k] for k in a.files}
        validate_bundle(graph,query)
        assert set(graph['drug_ids'])==set(sub[sub.split.eq('train')].drug_id)
        assert set(query['drug_ids'])==set(sub[sub.split.ne('train')].drug_id)
    checks['all_prepared_contexts_train_query_validated']=40
    text=(QA/'test_results.txt').read_text(encoding='utf-8');m=re.search(r'Ran (\d+) tests in ([\d.]+)s',text)
    assert m and m.group(1)=='35' and text.rstrip().endswith('OK')
    checks['tests']={'passed':35,'seconds':float(m.group(2)),'historical_WP08_tests_not_rerun':True,
        'development_failed_logs_retained':['test_first_run_failed.txt','test_second_run_failed.txt']}
    nb_path=ROOT/'notebooks/WP09_PPI_encoder_design.ipynb';nb=nbformat.read(nb_path,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];out=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,10))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in out)
    assert sum('image/png' in o.get('data',{}) for o in out)==7
    figures=ROOT/'reports/figures/WP09/design_v1'
    assert len(list(figures.glob('*.png')))==7
    html=(figures/'train_human_PPI_interactive.html').read_text(encoding='utf-8')
    assert not re.search(r'<script[^>]+src\s*=',html,re.I)
    checks['notebook']={'executed_cells':9,'embedded_PNG':7,'error_or_stderr':False,'sha256':sha(nb_path)}
    checks['figures']={'PNG_visual_review':7,'offline_embedded_HTML':1,'live_browser_interaction_test':False}
    quality=pd.read_csv(QA/'shuffle_quality.csv')
    counts=quality.groupby('threshold').status.apply(lambda s:int(s.eq('OK_degree_preserving_null').sum())).to_dict()
    assert counts=={400:0,700:39,900:32}
    checks['shuffle']={'accepted_by_threshold':{str(k):v for k,v in counts.items()},'accepted':71,'NA':49,
        'NA_not_replaced_by_real_edges':True,'uniform_mixing_proven':False}
    proposal=json.loads((ROOT/'configs/WP09_training_PROPOSED_v2.json').read_text(encoding='utf-8'))
    assert not proposal['training_enabled'] and proposal['threshold']['approved_primary'] is None
    checks['scope']={'design_data_encoder_complete':True,'training_performed':False,'performance_comparison':False,
        'selected_threshold':None,'proposed_threshold':700,'query_self_only':True,'K12_PPI_or_context':False,
        'gradient_checks_only_no_optimizer':True}
    checks['environment']={'python':platform.python_version()}
    for package in ('numpy','pandas','torch','networkx','matplotlib','plotly','nbformat'):
        checks['environment'][package]=importlib.metadata.version(package)
    json_write(QA/'environment.json',checks['environment'])
    files=list((ROOT/'scripts').glob('wp09*.py'))+[ROOT/'tests/test_wp09.py',
        ROOT/'configs/WP09_training_PROPOSED_v1.json',ROOT/'configs/WP09_training_PROPOSED_v2.json',
        ROOT/'reports/WP09.md',ROOT/'reports/WP09_PRETRAINING_DECISION_GATE.md',
        ROOT/'docs/plan/WP09_DESIGN_DATA_CONTRACT_v1.md']
    assert all(p.is_file() for p in files)
    checks['new_code_contract_report_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in files}
    checks['prepared_total_bytes']=sum(p.stat().st_size for p in (QA/'folds').glob('*.npz'))
    json_write(QA/'artifact_validation.json',checks)
    print(json.dumps({'preserved':checks['prior_files_unchanged'],'tests_passed':35,'executed_cells':9,
        'PNG':7,'shuffle_accepted':71,'shuffle_NA':49,'training':False,'threshold_approved':None}))


if __name__=='__main__':main()
