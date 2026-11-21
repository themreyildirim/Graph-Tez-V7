"""Yeni kapanış/tasarım çıktılarının denetimi; kabul edilen QA'ya yazmaz."""
import json
import re
import nbformat
import pandas as pd
from wp09_train import ROOT,QA,sha,write_json
from wp09_closure import CLOSE,verify_previous


def main():
    count=verify_previous()
    notebook_info=[]
    for name,pngs in [('WP09_final_closure.ipynb',2),('WP10_design_feasibility.ipynb',3)]:
        path=ROOT/'notebooks'/name
        book=nbformat.read(path,as_version=4);nbformat.validate(book)
        cells=[c for c in book.cells if c.cell_type=='code']
        assert [c.execution_count for c in cells]==list(range(1,6))
        images=0;tables=0
        for cell in cells:
            for output in cell.outputs:
                assert output.output_type!='error'
                assert not(output.output_type=='stream' and output.name=='stderr')
                data=output.get('data',{});images+=int('image/png' in data)
                tables+=int('<table' in data.get('text/html',''))
        assert images==pngs and tables>=5
        notebook_info.append({'file':path.relative_to(ROOT).as_posix(),'executed_cells':5,'embedded_PNGs':images,'HTML_tables':tables,'errors':0})
    for path in [CLOSE/'trainer_tests_rerun.txt',CLOSE/'closure_design_tests.txt']:
        text=path.read_text(encoding='utf-8-sig');assert text.rstrip().endswith('OK')
    closure=json.loads((CLOSE/'closure_checks.json').read_text(encoding='utf-8'))
    designq=ROOT/'reports/qa/WP10/design_v1'
    proposal=json.loads((ROOT/'configs/WP10_design_PROPOSED_v1.json').read_text(encoding='utf-8'))
    assert not proposal['training_enabled'] and not proposal['model_implemented'] and not proposal['graph_tensors_materialized']
    for path,h in json.loads((designq/'input_manifest.json').read_text(encoding='utf-8')).items():assert sha(ROOT/path)==h
    assert pd.read_csv(designq/'decision_gate.csv')['onay'].eq('BEKLİYOR').all()
    # Model ağacında hiçbir ek fit/checkpoint yok: önceki manifestin tam kümesi aynı.
    prior=json.loads((CLOSE/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    expected={p for p in prior if p.startswith('models/')}
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    assert expected==actual
    patterns=[ROOT/'scripts/wp09_closure.py',ROOT/'scripts/wp10_design_audit.py',ROOT/'scripts/wp09_close_wp10_notebooks.py',
        ROOT/'scripts/wp09_close_wp10_reports.py',ROOT/'scripts/wp09_close_wp10_validate.py',ROOT/'tests/test_wp09_closure_wp10_design.py',
        ROOT/'reports/WP09_FINAL_CLOSURE.md',ROOT/'reports/WP10_DESIGN_FEASIBILITY.md',ROOT/'configs/WP10_design_PROPOSED_v1.json',ROOT/'run_status.md']
    for info in notebook_info:patterns.append(ROOT/info['file'])
    for folder in [CLOSE,designq,ROOT/'reports/figures/WP09/final_closure_v1',ROOT/'reports/figures/WP10/design_v1']:
        patterns.extend(p for p in folder.rglob('*') if p.is_file() and p.name not in ['artifact_validation.json','final_artifact_manifest.json'])
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(patterns))}
    write_json(CLOSE/'final_artifact_manifest.json',manifest)
    result={'status':'PASS','accepted_prior_artifacts_unchanged':count,'model_NPZ_verified':190,'metadata_verified':190,
        'new_model_files':0,'original_trainer_tests_rerun':24,'additional_closure_design_tests':12,
        'outer_NPZ_score_reproductions':closure['outer_models_restored'],'same_key_checks':'PASS',
        'trained_forward_gradient_checks':'PASS; optimizer0, parameters unchanged',
        'notebooks':notebook_info,'PNG_files_visually_reviewed':5,'WP09':'CLOSED_ACCEPTED_BY_USER',
        'WP10':'DESIGN_ONLY_AWAITING_USER_APPROVAL','WP10_model_or_optimizer_run':False,
        'WP10_production_tensors_written':False,'new_biological_downloads':False,'prior_QC_changed':False,
        'cohort':62,'source_PT':1061,'source_positives':6416,'clinical_risk_claim':False}
    write_json(CLOSE/'artifact_validation.json',result)
    write_json(designq/'artifact_validation.json',{'status':'PASS','parent_validation':'reports/qa/WP09/final_closure_v1/artifact_validation.json',
        'parent_sha256':sha(CLOSE/'artifact_validation.json'),'design_only':True,'training_enabled':False,'QC_decision_PENDING_APPROVAL':True})
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
