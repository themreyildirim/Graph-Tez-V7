"""WP11 ilk aşama dosya/kanıt denetimi; önceki üreticileri çağırmaz."""
import json,sys
import nbformat
import pandas as pd
from wp11_linear_shap import ROOT,QA,sha,write_json,preserve
from wp11_shap_analysis import verify_manifest


def main():
    prior=json.loads((QA/'prior_artifacts_sha256.json').read_text());preserved=preserve()
    commits=verify_manifest('policy_commit_before_explanations.json');sources=verify_manifest('input_manifest.json')
    summary=json.loads((QA/'analysis_summary.json').read_text());assert not any(summary[k] for k in ['model_fit','graph_attribution','test_outcomes_read','WP12'])
    assert summary['models']==10 and summary['local_pairs']==27854 and summary['local_feature_rows']==167124
    nb=nbformat.read(ROOT/'notebooks/WP11_B1_SHAP.ipynb',as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];assert len(code)==8 and all(c.execution_count for c in code)
    outputs=[o for c in code for o in c.outputs];assert not any(o.output_type=='error' for o in outputs)
    images=sum('image/png' in o.get('data',{}) for o in outputs);assert images==6
    figures=sorted((ROOT/'reports/figures/WP11/B1_SHAP_v1').glob('*.png'));assert len(figures)==6 and all(p.stat().st_size>10000 for p in figures)
    log=(QA/'tests_v1.txt').read_text(encoding='utf-8');assert 'Ran 18 tests' in log and log.rstrip().endswith('OK') and log.count('... ok')==18
    chronology={'policy_commit_mtime_ns':(QA/'policy_commit_before_explanations.json').stat().st_mtime_ns,'first_local_table_mtime_ns':(QA/'local_shap.csv').stat().st_mtime_ns,'analysis_summary_mtime_ns':(QA/'analysis_summary.json').stat().st_mtime_ns,'interpretation':'Local filesystem execution-order record;not an external timestamp/notarization'}
    assert chronology['policy_commit_mtime_ns']<chronology['first_local_table_mtime_ns']<=chronology['analysis_summary_mtime_ns']
    write_json(QA/'execution_order_evidence.json',chronology)
    # Gelecek graf önerisi yalnız metadata/hash inceler; model forward çağrısı yok.
    graphmodels=[]
    for protocol in ['primary','stress']:
        for fold in range(1,6):
            mdpath=ROOT/f'models/WP10_factorial_training_v1/{protocol}_o{fold:02}_final_A1P1.json';md=json.loads(mdpath.read_text());npz=ROOT/md['parameters_file']
            assert md['variant']=='A1P1' and md['status']=='OK' and sha(npz)==md['parameters_sha256']
            graphmodels.append({'context':md['context'],'metadata_file':mdpath.relative_to(ROOT).as_posix(),'metadata_sha256':sha(mdpath),'model_file':npz.relative_to(ROOT).as_posix(),'parameters_sha256':sha(npz),'target_count':len(md['fitted_targets']),'use_in_WP11_stage1':'metadata/hash only;no graph attribution or forward'})
    write_json(QA/'graph_proposal_model_sources.json',graphmodels)
    archive=(QA/'run_status_before.md').read_bytes();current=(ROOT/'run_status.md').read_bytes();assert current.endswith(archive) and current!=archive
    coverage=pd.read_csv(QA/'coverage_summary.csv');assert coverage.groupby('protocol').test_explained.sum().to_dict()=={'primary':54,'stress':54};assert coverage.NA_PT.sum()==2
    validation={'status':'PASS','previous_accepted_files_unchanged':preserved,'frozen_policy_commit_entries':commits,'frozen_input_entries':sources,'selected_B1_outer_models':10,'explained_pairs':27854,'SHAP_feature_rows':167124,'tests_passed':18,'notebook_executed_code_cells':len(code),'notebook_embedded_PNG':images,'PNG_files_visually_reviewed':6,'model_fit_or_optimizer_steps_in_this_work':0,'graph_attribution_or_graph_forward_executed':False,'future_A1P1_model_metadata_hashes_verified':len(graphmodels),'prior_run_status_sha256':sha(QA/'run_status_before.md'),'prior_run_status_exact_bytes_retained':True,'all_previous_model_files_protected':sum(p.startswith('models/') for p in prior),'WP12_started':False}
    write_json(QA/'artifact_validation.json',validation)
    new=[]
    for folder in ['reports/qa/WP11','reports/figures/WP11']:
        new.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    new.extend([ROOT/p for p in ['reports/WP11.md','notebooks/WP11_B1_SHAP.ipynb','docs/plan/WP11_B1_SHAP_CONTRACT_v1.md','docs/plan/WP11_A1P1_GRAPH_EXPLANATION_CONTRACT_v1.md','scripts/wp11_linear_shap.py','scripts/wp11_shap_analysis.py','scripts/wp11_notebook.py','scripts/wp11_validate.py','tests/test_wp11_shap.py','run_status.md']])
    write_json(QA/'final_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(new)) if p.name!='final_artifact_manifest.json'})
    print(json.dumps(validation,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
