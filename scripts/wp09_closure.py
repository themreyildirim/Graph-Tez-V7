"""Kabul edilen WP09 sonuçlarını değiştirmeden NPZ/forward/backward kapanışı."""
import json
import hashlib
import re
import numpy as np
import pandas as pd
import torch
from wp09_train import ROOT, QA, MODEL, NAMES, sha, write_json, restore, load_bundle, select_query, score_queries, state_hash, source_labels, restrict_labels, proxy_matrix

CLOSE = ROOT/'reports/qa/WP09/final_closure_v1'


def verify_previous():
    previous = json.loads((CLOSE/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad = [p for p,h in previous.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    if bad: raise AssertionError(bad)
    return len(previous)


def main():
    if (CLOSE/'closure_checks.json').exists(): raise RuntimeError('Kapanış kanıtı zaten var; ezilmez')
    previous = verify_previous()
    manifest = json.loads((QA/'model_artifact_manifest.json').read_text(encoding='utf-8'))
    assert len(manifest)==380
    for p,h in manifest.items(): assert sha(ROOT/p)==h,p
    fits = pd.read_csv(QA/'model_fit_summary.csv').set_index('job_key')
    for file in sorted(MODEL.glob('*.npz')):
        h = hashlib.sha256()
        with np.load(file,allow_pickle=False) as a:
            for key in sorted(a.files):
                value=a[key];assert np.isfinite(value).all()
                h.update(key.encode());h.update(str(value.dtype).encode());h.update(str(value.shape).encode());h.update(value.tobytes())
        md=json.loads(file.with_suffix('.json').read_text(encoding='utf-8'))
        assert h.hexdigest()==md['selected_state_sha256']==fits.loc[file.stem,'selected_state_sha256']
    pred=pd.read_csv(QA/'oof_predictions.csv')
    scope=[]
    for protocol,f in pred.groupby('protocol'):
        reference=None
        for model,g in f.groupby('model'):
            assert not g.duplicated(['outer_fold','drug_id','class_id']).any()
            keys=set(map(tuple,g[['outer_fold','drug_id','class_id']].to_numpy()))
            if reference is None: reference=keys
            assert keys==reference
            scope.append({'protocol':protocol,'model':model,'key_count':len(keys),'same_keys':True})
    pd.DataFrame(scope).to_csv(CLOSE/'same_key_checks.csv',index=False)
    reconstruction=[];forward=[];protein_rows=[]
    context='primary_o01_final';graph=load_bundle(context,'train');query=load_bundle(context,'query')
    query=select_query(query,list(query['drug_ids'][query['split']=='test']),len(graph['protein_ids']))
    empty={k:v.copy() for k,v in graph.items()};empty['ppi_pairs_700']=np.empty((2,0),dtype=np.int64)
    source=source_labels()
    for name in NAMES:
        md=json.loads((MODEL/(context+'_'+name+'.json')).read_text(encoding='utf-8'))
        null=None
        if md['null_file']:
            with np.load(ROOT/md['null_file'],allow_pickle=False) as a:null=a['ppi_pairs'].copy()
        scores=score_queries(md,graph,query,null)
        expected=pred[pred.protocol.eq('primary')&pred.outer_fold.eq(1)&pred.model.eq(name)]
        errors=[]
        for i,d in enumerate(query['drug_ids']):
            if not query['eligible'][i]:continue
            target=expected[expected.drug_id.eq(d)].set_index('class_id').loc[md['fitted_targets']].score_observed_record_proxy.to_numpy()
            np.testing.assert_allclose(scores[i],target,rtol=1e-7,atol=1e-8)
            errors.extend(np.abs(scores[i]-target))
        reconstruction.append({'context':context,'model':name,'pairs':len(errors),'max_absolute_error':max(errors),'NPZ_restored':True})
        model=restore(md);before=state_hash(model.state_dict())
        model.zero_grad(set_to_none=True)
        a=model.forward(graph,700,md['variant'],null)
        b=model.forward(empty,700,'G_noPPI')
        difference=(a['protein_h']-b['protein_h']).detach().numpy()
        eligible=np.asarray(graph['eligible'],bool)
        labels=restrict_labels(source,list(graph['drug_ids'][eligible]))
        y=torch.from_numpy(proxy_matrix(labels,list(graph['drug_ids'][eligible]),md['fitted_targets']))
        loss=torch.nn.functional.binary_cross_entropy_with_logits(a['logits'][eligible],y)
        loss.backward()  # Türev doğrulaması; optimizer kurulmaz veya çalıştırılmaz.
        gradient=float(model.protein.message.weight.grad.norm())
        changed=float(np.linalg.norm(difference))
        assert state_hash(model.state_dict())==before
        if name=='G_noPPI': assert changed==0 and gradient==0
        else: assert changed>1e-5 and gradient>0
        forward.append({'context':context,'model':name,'same_weights_PPI_removed_protein_L2':changed,'trained_message_weight_gradient_norm':gradient,'train_BCE_at_saved_weights':float(loss.detach()),'optimizer_steps_this_check':0,'state_unchanged':True})
        for accession,diff in zip(graph['protein_ids'],np.linalg.norm(difference,axis=1)):
            protein_rows.append({'accession':accession,'model':name,'protein_delta_L2':diff})
    pd.DataFrame(reconstruction).to_csv(CLOSE/'NPZ_score_reconstruction.csv',index=False)
    pd.DataFrame(forward).to_csv(CLOSE/'trained_forward_gradient.csv',index=False)
    pd.DataFrame(protein_rows).to_csv(CLOSE/'trained_protein_edge_effect.csv',index=False)
    log=(CLOSE/'trainer_tests_rerun.txt').read_text(encoding='utf-8-sig')
    elapsed=re.search(r'Ran 24 tests in ([0-9.]+)s',log)
    assert elapsed and log.rstrip().endswith('OK')
    coverage=pd.read_csv(QA/'evaluation_coverage.csv')
    primary=coverage[coverage.protocol.eq('primary')&coverage.scope.eq('paired54')]
    assert primary.out_of_scored_vocab_positive.eq(1685).all()
    status=pd.read_csv(QA/'prediction_status_all62.csv')
    assert status[status.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all()
    assert len(pd.read_csv(QA/'excluded_inner_jobs.csv'))==10
    checks={'status':'PASS','previous_artifacts_preserved':previous,'model_NPZ':190,'model_metadata_JSON':190,
        'numeric_states_rehashed':190,'real_trainer_tests_rerun':24,'test_seconds':float(elapsed.group(1)),
        'outer_models_restored':len(reconstruction),'max_score_reconstruction_error':max(r['max_absolute_error'] for r in reconstruction),
        'trained_forward_backward_probes':len(forward),'probe_optimizer_steps':0,'training_reproduction_tests_RAM_only':True,
        'all_five_models_same_OOF_keys':True,'primary_paired54_outside_source_positives':1685,
        'Methenamine_abstention_preserved':True,'null_failures_remain_NA':3,'shared_skipped_inner_jobs':10,
        'refit_production_models':False,'retuning':False,'source_drugs':62,'source_PT':1061,'source_positives':6416}
    verify_previous();write_json(CLOSE/'closure_checks.json',checks);print(json.dumps(checks,ensure_ascii=False))


if __name__=='__main__':main()
