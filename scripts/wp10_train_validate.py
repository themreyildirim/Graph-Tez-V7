"""Gerçek eğitim sonuçlarının son dosya ve notebook denetimi;refit yapmaz."""
import json,re,importlib.metadata,platform
import nbformat
import numpy as np
import pandas as pd
from wp10_train import ROOT,QA,MODEL,NAMES,preserve,sha,write_json,state_hash,restore


def main():
    prior=preserve()
    for name in ['input_manifest.json','model_artifact_manifest.json','code_contract_before_fit.json']:
        expected=json.loads((QA/name).read_text(encoding='utf-8'))
        for path,value in expected.items():assert sha(ROOT/path)==value,path
    old=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    manifest=json.loads((QA/'model_artifact_manifest.json').read_text(encoding='utf-8'))
    assert len(manifest)==304
    expected_models={p for p in old if p.startswith('models/')}|set(manifest)
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    assert expected_models==actual
    fit=pd.read_csv(QA/'model_fit_summary.csv');assert len(fit)==152 and fit.status.eq('OK').all()
    assert int(fit.optimizer_steps.sum())==8611
    for path in MODEL.glob('*.json'):
        md=json.loads(path.read_text(encoding='utf-8'));model=restore(md)
        assert state_hash(model.state_dict())==md['selected_state_sha256']
        assert sha(ROOT/md['parameters_file'])==md['parameters_sha256']
        assert md['approved_run_config_sha256']==sha(QA/'run_config.json')
        assert md['model'] in NAMES and md['null_file']==''
    assert fit.groupby('context').initial_state_sha256.nunique().eq(1).all()
    commit=json.loads((QA/'selection_complete_before_test_scoring.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in commit['selections'].items())
    scoring=json.loads((QA/'scoring_complete.json').read_text(encoding='utf-8'))
    assert scoring['selection_commit_sha256']==sha(QA/'selection_complete_before_test_scoring.json')
    assert scoring['model_manifest_sha256']==sha(QA/'model_artifact_manifest.json')
    assert scoring['outer_decisions_sha256_unchanged']==commit['outer_epoch_decisions_sha256']==sha(QA/'outer_fit_and_selection.json')
    assert scoring['predictions_sha256']==sha(QA/'oof_predictions.csv')
    evaluation=json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))
    assert evaluation['OOF_sha256']==sha(QA/'oof_predictions.csv') and evaluation['no_refit'] and not evaluation['shuffled_PPI_experiments']
    assert pd.read_csv(QA/'excluded_comparison_keys.csv').empty
    assert len(pd.read_csv(QA/'excluded_inner_jobs.csv'))==8
    assert pd.read_csv(QA/'bootstrap_validity.csv').valid_replicates.eq(1000).all()
    text=(QA/'tests_actual_trainer.txt').read_text(encoding='utf-8-sig');test=re.search(r'Ran 19 tests in ([0-9.]+)s',text)
    assert test and text.rstrip().endswith('OK')
    notebook_path=ROOT/'notebooks/WP10_factorial_training.ipynb';book=nbformat.read(notebook_path,as_version=4);nbformat.validate(book)
    cells=[c for c in book.cells if c.cell_type=='code'];assert [c.execution_count for c in cells]==list(range(1,10))
    pngs=0;tables=0
    for cell in cells:
        for output in cell.outputs:
            assert output.output_type!='error'
            assert not(output.output_type=='stream' and output.name=='stderr')
            data=output.get('data',{});pngs+=int('image/png' in data);tables+=int('<table' in data.get('text/html',''))
    assert pngs==7 and tables>=12
    figures=ROOT/'reports/figures/WP10/training_v1';assert len(list(figures.glob('*.png')))==7
    environment={'python':platform.python_version(),'CPU_threads':1}
    for package in ['torch','numpy','pandas','scikit-learn','scipy','matplotlib','nbformat']:
        environment[package]=importlib.metadata.version(package)
    environment['PyG']='2.8.0 from existing project .deps/pyg';environment['RDKit']='2026.09.1 from existing project .deps/rdkit'
    write_json(QA/'environment.json',environment)
    files=list((ROOT/'scripts').glob('wp10_train*.py'))+[ROOT/'tests/test_wp10_training.py',ROOT/'tests/test_wp10_training_preflight.py',notebook_path,
        ROOT/'reports/WP10_TRAINING_RESULTS.md',ROOT/'reports/WP10_TRAINING_MODEL_CARD.md',ROOT/'run_status.md']
    files+=list(figures.glob('*.png'))
    files +=[p for p in QA.rglob('*') if p.is_file() and p.name not in ['artifact_validation.json','final_artifact_manifest.json']]
    write_json(QA/'final_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))})
    result={'status':'PASS','version':'WP10-factorial-training-v1','previous_files_unchanged':prior,'trained_NPZ':152,'metadata_JSON':152,
        'numeric_model_states_rehashed':152,'production_optimizer_steps':int(fit.optimizer_steps.sum()),'all_fit_status':'OK',
        'trainer_tests':19,'test_seconds':float(test.group(1)),'same_shared_keys':True,'excluded_comparison_keys':0,'bootstrap_replicates':1000,
        'notebook_executed_cells':9,'embedded_PNGs':pngs,'HTML_tables':tables,'PNG_files_visually_reviewed':7,
        'real_artifact_example_drug':'DB00199 Erythromycin,primary_o03_final,preselected before results',
        'shuffled_WP10_experiments':False,'baseline_and_WP09_refits':False,'QC_changed':False,'clinical_risk_claim':False,
        'WP11_started':False,'status_next':'AWAITING_USER_RESULTS_REVIEW'}
    preserve();write_json(QA/'artifact_validation.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
