"""WP11 graph uygulama kanıtı; nihai WP11 kapanışı veya eğitim yapmaz."""
import gzip,json,re
import nbformat
import pandas as pd
from wp11_graph_policy import ROOT,QA,preserve,verify
from wp11_linear_shap import sha,write_json


def main():
    preserved=preserve();verify('policy_commit_before_attribution.json');sources=verify('input_manifest.json')
    complete=json.loads((QA/'analysis_complete.json').read_text());assert complete['status']=='PASS' and not complete['new_training'] and not complete['WP11_final_closed'] and not complete['WP12'] and complete['guarded_fit_optimizer_backward_calls']==0
    # B1'nin önceki manifestindeki mutable status dosyası bu görevin başında arşivlendi.
    b1=ROOT/'reports/qa/WP11/B1_SHAP_v1/final_artifact_manifest.json';bm=json.loads(b1.read_text());bad=[]
    for p,h in bm.items():
        actual=QA/'run_status_before.md' if p=='run_status.md' else ROOT/p
        if sha(actual)!=h:bad.append(p)
    assert not bad,bad
    history=(QA/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes().endswith(history) and (ROOT/'run_status.md').read_bytes()!=history
    for name,n in [('synthetic_tests_before_real.txt',10),('real_tests_v1.txt',16)]:
        log=(QA/name).read_text(encoding='utf-8');assert f'Ran {n} tests' in log and log.rstrip().endswith('OK') and log.count('... ok')==n
    gate=json.loads((QA/'synthetic_gate_PASS.json').read_text());start=json.loads((QA/'real_attribution_started.json').read_text());assert gate['gate_time_ns']<start['time_ns']<complete['completed_time_ns']
    assert (QA/'policy_commit_before_attribution.json').stat().st_mtime_ns<gate['gate_time_ns']
    failure=QA/'attempt_01_technical_failure';assert (failure/'failure_evidence.json').exists()
    for name in ['role_contributions.csv.gz','ppi_contributions.csv.gz']:assert gzip.open(failure/name,'rt').read()==''
    nb=nbformat.read(ROOT/'notebooks/WP11_A1P1_graph_explanations.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];outputs=[o for c in code for o in c.outputs];assert len(code)==9 and all(c.execution_count for c in code) and not any(o.output_type=='error' for o in outputs)
    images=sum('image/png' in o.get('data',{}) for o in outputs);assert images==6
    pngs=list((ROOT/'reports/figures/WP11/graph_v1').glob('*.png'));assert len(pngs)==6 and all(p.stat().st_size>10000 for p in pngs)
    c=pd.read_csv(QA/'consistency_checks.csv');st=pd.read_csv(QA/'stability_checks.csv');extra=pd.read_csv(QA/'additional_delta_stability.csv');stream=pd.read_csv(QA/'compressed_table_stream_checks.csv')
    assert len(c)==10 and c.model_graph_query_cache_unchanged.all() and c.OOF_pairs_checked.sum()==35974
    assert c.reference_logit_error.max()==c.original_cache_error.max()==c.repeat_error.max()==c.other_query_role_isolation_error.max()==0
    assert c.OOF_score_error.max()<=1e-7 and st.max_abs_logit_error.max()<=1e-5 and extra.max_abs_error.max()<=1e-5
    assert int(stream.rows.sum())==2440976 and stream.max_delta_identity_roundtrip_error.max()<=1e-5
    inventory=pd.read_csv(QA/'all_drug_scope_named.csv');assert len(inventory)==124
    for p,d in inventory.groupby('protocol'):
        assert len(d)==62 and d.eligible.sum()==61 and d.atom_QC_available.sum()==54 and d.role_relations.gt(0).sum()==60 and d.applicable_PPI_pairs.gt(0).sum()==51
    metadata=json.loads((ROOT/'reports/qa/WP10/training_v1/training_complete.json').read_text());assert (metadata['source_drugs'],metadata['source_PT'],metadata['source_positives'])==(62,1061,6416)
    previous=json.loads((QA/'prior_artifacts_sha256.json').read_text())
    result={'status':'PASS','graph_application_complete_for_user_review':True,'WP11_final_closed':False,'WP12':False,'preserved_previous_files':preserved,'preserved_previous_model_metadata_files':sum(p.startswith('models/') for p in previous),'B1_stage1_manifest_entries_unchanged':len(bm),'source_input_hashes_verified':sources,'outer_A1P1_models':10,'source_drugs':62,'source_PT':1061,'source_positives':6416,'original_OOF_pairs_checked':35974,'role_contribution_rows':557574,'PPI_contribution_rows':1883402,'synthetic_tests_passed_before_real':10,'real_tests_passed':16,'additional_delta_stability_checks':len(extra),'max_delta_stability_error':extra.max_abs_error.max(),'executed_notebook_cells':9,'embedded_images':images,'PNG_files_visually_reviewed':6,'training_optimizer_backward_calls':0,'technical_failed_attempts_retained':1,'failed_attempt_contribution_rows':0,'unresolved_failures':0,'old_run_status_bytes_retained':True,'semantics':'observed-record single-message delta logit;NOT SHAP,causality,clinical risk'}
    write_json(QA/'artifact_validation.json',result)
    files=[p for p in QA.rglob('*') if p.is_file() and p.name!='final_artifact_manifest.json']
    files+=list((ROOT/'reports/figures/WP11/graph_v1').glob('*.png'))
    files+=list((ROOT/'scripts').glob('wp11_graph*.py'))+list((ROOT/'tests').glob('test_wp11_graph*.py'))
    files+=[ROOT/'notebooks/WP11_A1P1_graph_explanations.ipynb',ROOT/'reports/WP11_GRAPH_EXPLANATIONS.md',ROOT/'run_status.md']
    write_json(QA/'final_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)})
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
