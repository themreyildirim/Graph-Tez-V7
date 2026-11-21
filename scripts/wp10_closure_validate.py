"""Kapanış belgeleri/notebook ve önceki dosyaların son salt okunur denetimi."""
import json
import nbformat
import pandas as pd
from wp10_final_closure import ROOT,CLOSE,preserve
from wp10_train import QA,sha,write_json


def main():
    previous=preserve()
    archived=(CLOSE/'run_status_before.md').read_bytes()
    assert (ROOT/'run_status.md').read_bytes().endswith(archived)
    authorization=json.loads((CLOSE/'authorization.json').read_text(encoding='utf-8'))
    assert sha(CLOSE/'run_status_before.md')==authorization['run_status_before_sha256']
    snapshot=json.loads((CLOSE/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    assert {p for p in snapshot if p.startswith('models/')}=={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    checks=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
    assert checks['current_readonly_tests']['executed']==13 and checks['current_readonly_tests']['fit_optimizer_guard_calls']==0
    assert checks['current_optimizer_steps']==checks['current_model_fit_calls']==0
    selection=pd.read_csv(CLOSE/'test_selection.csv');assert len(selection)==19 and int(selection.executed_this_closure.sum())==13
    assert (CLOSE/'readonly_tests_rerun.txt').read_text(encoding='utf-8').rstrip().endswith('OK')
    assert sha(QA/'tests_actual_trainer.txt')==checks['original_tests']['log_sha256_unchanged']
    modelchecks=pd.read_csv(CLOSE/'model_hash_checks_all152.csv');assert len(modelchecks)==152 and modelchecks.status.eq('PASS').all()
    reconstruction=pd.read_csv(CLOSE/'OOF_reconstruction_all40_outer.csv')
    assert len(reconstruction)==40 and reconstruction.OOF_pairs_verified.sum()==143896
    assert reconstruction.max_absolute_error.le(1e-7).all() and not reconstruction.refit.any()
    scope=json.loads((CLOSE/'WP11_roadmap_scope.json').read_text(encoding='utf-8'))
    assert sha(ROOT/scope['source'])==scope['source_sha256'] and not scope['implementation_started']
    assert scope['exact_WP11_row'] in (ROOT/scope['source']).read_text(encoding='utf-8')
    notebook=ROOT/'notebooks/WP10_final_closure.ipynb';book=nbformat.read(notebook,as_version=4);nbformat.validate(book)
    cells=[c for c in book.cells if c.cell_type=='code'];assert [c.execution_count for c in cells]==[1,2,3,4]
    pngs=0;tables=0
    for cell in cells:
        for output in cell.outputs:
            assert output.output_type!='error' and not(output.output_type=='stream' and output.name=='stderr')
            data=output.get('data',{});pngs+=int('image/png' in data);tables+=int('<table' in data.get('text/html',''))
    assert pngs==2 and tables>=8
    figures=ROOT/'reports/figures/WP10/final_closure_v1';assert len(list(figures.glob('*.png')))==2
    paths=[ROOT/'scripts/wp10_final_closure.py',ROOT/'scripts/wp10_closure_documents.py',ROOT/'scripts/wp10_closure_notebook.py',ROOT/'scripts/wp10_closure_validate.py',
        ROOT/'reports/WP10_FINAL_CLOSURE.md',ROOT/'reports/WP11_PREPARATION_DECISION.md',ROOT/'run_status.md',notebook]
    paths+=list(figures.glob('*.png'))
    paths+=[p for p in CLOSE.rglob('*') if p.is_file() and p.name not in ['artifact_validation.json','final_artifact_manifest.json']]
    write_json(CLOSE/'final_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))})
    result={'status':'PASS','WP10':'CLOSED_ACCEPTED_BY_USER','WP11':'PREPARATION_REPORT_ONLY;NOT_IMPLEMENTED',
        'previous_artifacts_unchanged':previous,'prior_run_status_archived_and_preserved':True,'registered_models_verified':152,'outer_models_reconstructed':40,
        'OOF_pairs_verified':143896,'OOF_max_error':float(reconstruction.max_absolute_error.max()),'read_only_tests_rerun':13,'original_tests_record_verified':19,
        'model_fit_calls':0,'optimizer_steps':0,'new_model_files':0,'SHAP_or_attribution_run':False,'results_replaced':False,
        'notebook_executed_cells':4,'notebook_PNGs':pngs,'HTML_tables':tables,'PNG_files_visually_reviewed':2,
        'active_roadmap_unchanged':True,'model_source_QC_unchanged':True,'clinical_risk_claim':False,'awaiting_user_direction':True}
    preserve();write_json(CLOSE/'artifact_validation.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
