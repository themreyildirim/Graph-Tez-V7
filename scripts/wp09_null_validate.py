"""Null v3 kapanışı: önceki artefaktlar + test/notebook + kapalı eğitim onayı."""
import json,re,ast
import numpy as np
import pandas as pd
import nbformat
from wp09_null_gate import ROOT,QA,CONFIG,preserve,sha,write_json


def main():
    checks={'prior_files_unchanged':preserve()}
    protected=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    expected={p for p in protected if p.startswith('models/')}
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    assert actual==expected
    checks['model_artifact_membership_unchanged']=len(actual)
    for name in ('input_manifest.json','schedule_input_manifest.json'):
        paths=json.loads((QA/name).read_text(encoding='utf-8'))
        assert all(sha(ROOT/p)==h for p,h in paths.items())
        checks[name]={'entries':len(paths),'changed':[]}
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    policy=json.loads((QA/'policy_before_new_null_results.json').read_text(encoding='utf-8'))
    assert sha(CONFIG)==policy['configuration_sha256']
    assert not config['training_enabled'] and config['threshold']['recommended_primary']==700
    assert config['threshold']['approved_primary'] is None
    candidates=pd.read_csv(QA/'null_preflight_700_three_replicates.csv',keep_default_na=False)
    assert len(candidates)==120 and candidates.status.eq('OK_degree_preserving_null').sum()==117
    for row in candidates.itertuples():
        if row.status=='OK_degree_preserving_null':assert row.artifact_file and sha(ROOT/row.artifact_file)==row.artifact_sha256
        else:assert not row.artifact_file and not row.artifact_sha256
    checks['nulls']={'threshold':700,'contexts':40,'replicates':3,'accepted':117,'NA':3,
        'old_R0_unchanged':True,'no_NA_substitution':True,'generator_budget_or_seed_search':False}
    tests=(QA/'test_results.txt').read_text(encoding='utf-8');m=re.search(r'Ran ([0-9]+) tests in ([0-9.]+)s',tests)
    assert m and m.group(1)=='18' and tests.rstrip().endswith('OK')
    checks['tests']={'passed':18,'seconds':float(m.group(2)),'previous_encoder35_preserved_not_rerun':True}
    nb_path=ROOT/'notebooks/WP09_null_policy_review.ipynb'
    nb=nbformat.read(nb_path,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs]
    assert [c.execution_count for c in code]==list(range(1,8))
    assert not any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs)
    assert sum('image/png' in o.get('data',{}) for o in outputs)==4
    assert len(list((ROOT/'reports/figures/WP09/null_gate_v3').glob('*.png')))==4
    checks['notebook']={'executed_cells':7,'embedded_PNG':4,'errors_or_stderr':False,'sha256':sha(nb_path)}
    checks['figures']={'PNG_visually_reviewed':4,'interactive_HTML':'not needed for static topology/missingness teaching'}
    scope=pd.read_csv(QA/'common_inner_outer_preflight.csv')
    assert len(scope)==10 and scope.common_valid_inner_count.ge(2).all() and scope.outer_all_three_nulls_valid.all()
    schedule=pd.read_csv(QA/'training_sequence_PREVIEW_ONLY.csv')
    assert len(schedule)==190 and schedule.status.eq('NOT_RUN_AWAITING_USER_APPROVAL').all()
    checks['scope']={'outer_topology_ready':10,'common_inner_contexts':int(scope.common_valid_inner_count.sum()),
        'excluded_inner_contexts':2,'future_fit_jobs_preview':190,'executed_fit_jobs':0,
        'optimizer_or_real_PT_scores':False,'model_metric_evaluability_not_yet_checked':True,
        'model_type':'protein-PPI message-passing with scalar chemistry; no molecular atom-bond GNN',
        'training_authorized':False}
    files=list((ROOT/'scripts').glob('wp09_null_*.py'))+[ROOT/'tests/test_wp09_null_gate.py',CONFIG,
        ROOT/'reports/WP09_FINAL_TRAINING_GATE.md']
    checks['new_code_report_contract_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in files}
    write_json(QA/'artifact_validation.json',checks)
    write_json(QA/'method_references.json',{'biological_dataset_download':False,'purpose':'methods only',
        'URLs':['https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.swap.double_edge_swap.html',
            'https://arxiv.org/abs/1608.00607','https://arxiv.org/abs/2105.12120']})
    print(json.dumps({'preserved':checks['prior_files_unchanged'],'tests':18,'notebook_cells':7,
        'PNG':4,'null_accepted':117,'null_NA':3,'outer_topology_ready':10,'training':False}))


if __name__=='__main__':main()
