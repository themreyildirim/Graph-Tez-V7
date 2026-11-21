"""WP10 kapanışı: kayıtlı artefakt denetimi ve yalnız fit içermeyen eski testler."""
import io,json,re,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import wp10_train as t
from wp10_molecular_graph import numeric_digest

ROOT=t.ROOT;CLOSE=ROOT/'reports/qa/WP10/final_closure_v1'


def preserve():
    previous=json.loads((CLOSE/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if not (ROOT/p).is_file() or t.sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(previous)


def readonly_tests():
    sys.path.insert(0,str(ROOT/'tests'))
    from test_wp10_training import ActualFactorialTrainerTests
    from test_wp10_training_preflight import TrainingPreflight
    loader=unittest.TestLoader();suite=unittest.TestSuite();selection=[]
    for cls in [ActualFactorialTrainerTests,TrainingPreflight]:
        for name in loader.getTestCaseNames(cls):
            selected=(cls is ActualFactorialTrainerTests and not name.startswith('test_07_')) or (cls is TrainingPreflight and name.startswith('test_02_'))
            selection.append({'test_class':cls.__name__,'test_name':name,'executed_this_closure':selected,
                'reason':'read-only existing-model/source/OOF check' if selected else 'trainer/backward path excluded under current no-refit instruction; original passed log retained'})
            if selected:suite.addTest(cls(name))
    pd.DataFrame(selection).to_csv(CLOSE/'test_selection.csv',index=False)
    calls=[]
    def forbidden(*args,**kwargs):
        calls.append('FORBIDDEN_FIT_OR_OPTIMIZER_CALL');raise AssertionError('Closure explicitly forbids fitting and optimizer construction')
    started=time.perf_counter()
    with (CLOSE/'readonly_tests_rerun.txt').open('w',encoding='utf-8') as log:
        with patch.object(t,'fit_model',forbidden),patch.object(t,'training',forbidden),patch.object(t,'run_job',forbidden),patch.object(t.torch.optim,'AdamW',forbidden):
            result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not result.wasSuccessful() or calls:raise AssertionError('Read-only test suite failed;see new closure log')
    return {'executed':result.testsRun,'passed':result.testsRun,'original_total':19,'not_rerun':19-result.testsRun,
        'fit_optimizer_guard_calls':len(calls),'seconds':time.perf_counter()-started}


def main():
    if (CLOSE/'closure_checks.json').exists():raise RuntimeError('Kapanış v1 zaten var;eski kanıtı ezme')
    previous=preserve();t.configure_runtime()
    checks=[]
    for name in ['input_manifest.json','model_artifact_manifest.json','code_contract_before_fit.json','final_artifact_manifest.json']:
        manifest=json.loads((t.QA/name).read_text(encoding='utf-8'));bad=[]
        for p,h in manifest.items():
            path=CLOSE/'run_status_before.md' if p=='run_status.md' else ROOT/p
            if not path.is_file() or t.sha(path)!=h:bad.append(p)
        assert not bad,(name,bad)
        checks.append({'manifest':name,'files_verified':len(manifest),'status':'PASS','historical_run_status_verified_from_archive':name=='final_artifact_manifest.json'})
    pd.DataFrame(checks).to_csv(CLOSE/'manifest_checks.csv',index=False)
    rows=[]
    for path in sorted(t.MODEL.glob('*.json')):
        m=json.loads(path.read_text(encoding='utf-8'))
        with np.load(ROOT/m['parameters_file'],allow_pickle=False) as a:
            arrays={k:a[k].copy() for k in a.files};assert all(np.isfinite(x).all() for x in arrays.values())
        digest=numeric_digest(arrays);assert digest==m['selected_state_sha256']
        assert t.sha(ROOT/m['parameters_file'])==m['parameters_sha256']
        rows.append({'model_job':m['job_key'],'model':m['model'],'context':m['context'],'numeric_state_sha256':digest,
            'weights_file_sha256':t.sha(ROOT/m['parameters_file']),'metadata_sha256':t.sha(path),'status':'PASS'})
    assert len(rows)==152
    pd.DataFrame(rows).to_csv(CLOSE/'model_hash_checks_all152.csv',index=False)
    oldlog=(t.QA/'tests_actual_trainer.txt').read_text(encoding='utf-8-sig')
    original=re.search(r'Ran 19 tests in ([0-9.]+)s',oldlog);assert original and oldlog.rstrip().endswith('OK')
    tests=readonly_tests()
    # Bütün outer kayıtları tekrar okunur;skorlar karşılaştırılır,OOF dosyası yazılmaz.
    pred=pd.read_csv(t.QA/'oof_predictions.csv');reconstruction=[]
    for path in sorted(t.MODEL.glob('*_final_*.json')):
        m=json.loads(path.read_text(encoding='utf-8'));g=t.load_bundle(m['context'],'train');q=t.load_bundle(m['context'],'query')
        q=t.select_query(q,list(q['drug_ids'][q['split']=='test']),len(g['protein_ids']))
        actual=t.score_queries(m,g,q)
        saved=pred[pred.protocol.eq(m['protocol'])&pred.outer_fold.eq(m['outer_fold'])&pred.model.eq(m['model'])]
        errors=[]
        for i,d in enumerate(q['drug_ids']):
            if not q['eligible'][i]:continue
            expected=saved[saved.drug_id.eq(d)].set_index('class_id').loc[m['fitted_targets']].score_observed_record_proxy.to_numpy()
            np.testing.assert_allclose(actual[i],expected,rtol=1e-7,atol=1e-8)
            errors.extend(np.abs(actual[i]-expected))
        assert len(errors)==len(saved)
        reconstruction.append({'job':m['job_key'],'protocol':m['protocol'],'model':m['model'],'outer_fold':m['outer_fold'],
            'OOF_pairs_verified':len(errors),'max_absolute_error':max(errors),'refit':False})
    assert len(reconstruction)==40 and sum(r['OOF_pairs_verified'] for r in reconstruction)==len(pred)==143896
    pd.DataFrame(reconstruction).to_csv(CLOSE/'OOF_reconstruction_all40_outer.csv',index=False)
    keys=pd.read_csv(t.QA/'comparison_keys.csv');keyrows=[]
    for (protocol,scope),sub in keys.groupby(['protocol','scope']):
        expected=set(map(tuple,sub[['outer_fold','drug_id','class_id']].to_numpy()))
        for model in t.NAMES:
            scores=pred[pred.protocol.eq(protocol)&pred.model.eq(model)]
            actual=set(map(tuple,scores[['outer_fold','drug_id','class_id']].to_numpy()))
            assert expected<=actual
            keyrows.append({'protocol':protocol,'scope':scope,'model':model,'shared_keys_verified':len(expected),'status':'PASS'})
    pd.DataFrame(keyrows).to_csv(CLOSE/'comparison_key_checks.csv',index=False)
    status=pd.read_csv(t.QA/'prediction_status_all62.csv');assert status[status.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all()
    coverage=pd.read_csv(t.QA/'evaluation_coverage.csv');assert coverage[coverage.protocol.eq('primary')&coverage.scope.eq('paired54')].out_of_scored_vocab_positive.eq(1685).all()
    scoring=json.loads((t.QA/'scoring_complete.json').read_text(encoding='utf-8'));evaluation=json.loads((t.QA/'evaluation_complete.json').read_text(encoding='utf-8'))
    assert scoring['predictions_sha256']==evaluation['OOF_sha256']==t.sha(t.QA/'oof_predictions.csv')
    fit=pd.read_csv(t.QA/'model_fit_summary.csv');assert fit.status.eq('OK').all()
    result={'status':'PASS','WP10':'CLOSED_ACCEPTED_BY_USER','WP11':'ROADMAP_PREPARATION_ONLY_NOT_IMPLEMENTED',
        'accepted_prior_artifacts_preserved':preserve(),'registered_NPZ_verified':152,'metadata_JSON_verified':152,
        'numeric_states_rehashed':152,'outer_models_reconstructed':40,'OOF_pairs_reconstructed':len(pred),
        'OOF_max_absolute_error':max(r['max_absolute_error'] for r in reconstruction),'same_comparison_keys':True,
        'original_tests':{'passed':19,'seconds':float(original.group(1)),'log_sha256_unchanged':t.sha(t.QA/'tests_actual_trainer.txt')},
        'current_readonly_tests':tests,'current_optimizer_steps':0,'current_model_fit_calls':0,'metrics_replaced':False,
        'historical_production_optimizer_steps':int(fit.optimizer_steps.sum()),'source_drugs':62,'source_PT':1061,'source_positives':6416,
        'primary_paired54_outside_positives':1685,'clinical_risk_claim':False,'SHAP_or_graph_attribution_run':False}
    t.write_json(CLOSE/'closure_checks.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
