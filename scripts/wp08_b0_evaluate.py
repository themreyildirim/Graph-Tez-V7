"""B0 keşifsel eşleştirilmiş değerlendirme; B1/B2 skorları salt okunur."""
import json,time
import numpy as np
import pandas as pd
from wp08_b0_frequency import ROOT,PREP,BASE,QA,POLICY,SEMANTICS,write_csv,write_json,sha,check_preservation
from wp08_baseline_metrics import MetricPanel,METRICS,grouped_bootstrap_weights,percentile_interval


def lookup_truth():
    source=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','meddra_cui','conservative'])
    source=source[source.conservative]
    return {c:set(f.id) for c,f in source.groupby('meddra_cui')}


def scoped_reference_rows(predictions,protocol,scope,complete_ids):
    """Frozen scored key masks, not filtered by outcome values."""
    frame=predictions[predictions.protocol.eq(protocol)&predictions.family.eq('PT')]
    keys=['outer_fold','drug_id','class_id']
    a=frame[frame.model.eq('B1')];b=frame[frame.model.eq('B2')]
    if scope=='own_B1':return a[keys].copy(),{'B1':a}
    if scope=='own_B2':return b[keys].copy(),{'B2':b}
    common=a[keys].merge(b[keys],on=keys,how='inner',validate='one_to_one')
    if scope=='complete_case53':common=common[common.drug_id.isin(complete_ids)]
    if scope not in ('paired54','complete_case53'):raise ValueError('Unknown scope')
    return common,{'B1':a.merge(common,on=keys,validate='one_to_one'),
                   'B2':b.merge(common,on=keys,validate='one_to_one')}


def build_panels(keys,baseline_frames,b0_scores,ids,truth,scope,reference_names=None):
    classes=sorted(keys.class_id.unique());ci={c:i for i,c in enumerate(classes)};di={d:i for i,d in enumerate(ids)}
    y=np.array([[int(d in truth.get(c,set())) for c in classes] for d in ids],dtype=np.int8)
    panels={}
    for model,frame in baseline_frames.items():
        scores=np.full(y.shape,np.nan)
        for r in frame.itertuples():scores[di[r.drug_id],ci[r.class_id]]=r.score_observed_record_proxy
        panels[model]=MetricPanel(y,scores,ids,classes)
    references=['B0_all_train','B0_like_B1','B0_like_B2']
    if scope=='own_B1':references=['B0_all_train','B0_like_B1']
    if scope=='own_B2':references=['B0_all_train','B0_like_B2']
    if reference_names is not None:references=list(reference_names)
    for model in references:
        scores=np.full(y.shape,np.nan)
        joined=keys.merge(b0_scores[b0_scores.reference.eq(model)],on=['outer_fold','drug_id','class_id'],how='left',validate='one_to_one')
        if joined.frequency_score.isna().any():raise ValueError('Missing frozen B0 target score')
        for r in joined.itertuples():scores[di[r.drug_id],ci[r.class_id]]=r.frequency_score
        panels[model]=MetricPanel(y,scores,ids,classes)
    first=next(iter(panels.values())).mask
    if any(not np.array_equal(first,p.mask) for p in panels.values()):raise ValueError('Unpaired drug/target scope')
    return panels


def main():
    check_preservation()
    policy=json.loads((QA/'policy_before_B0_results.json').read_text(encoding='utf-8'))
    if policy!=POLICY:raise RuntimeError('B0 policy changed')
    frequency_hash=sha(QA/'train_frequency_estimates.csv');query_hash=sha(QA/'B0_outer_query_scores.csv')
    predictions=pd.read_csv(BASE/'oof_predictions.csv');predictions=predictions[predictions.family.eq('PT')]
    b0=pd.read_csv(QA/'B0_outer_query_scores.csv').rename(columns={'pt_cui':'class_id'})
    outer=pd.read_csv(PREP/'outer_membership_v1.csv')
    complete=pd.read_csv(PREP/'complete_case_53_inventory_ONLY.csv');complete_ids=set(complete[complete.complete_case_sensitivity].drug_id)
    truth=lookup_truth();metric_rows=[];deltas=[];drug_rows=[];class_rows=[];fold_rows=[];coverage=[];raw_scores=[]
    start=time.perf_counter()
    for pi,protocol in enumerate(('primary','stress')):
        membership=outer[outer.protocol.eq(protocol)].sort_values('drug_id');ids=list(membership.drug_id)
        groups=dict(zip(membership.drug_id,membership.group_id));folds=dict(zip(membership.drug_id,membership.outer_test_fold))
        weights=grouped_bootstrap_weights(ids,groups,policy['bootstrap_reps'],policy['seed']+9000+pi)
        for scope in ('own_B1','own_B2','paired54','complete_case53','B0_all62_reference_ONLY'):
            source_b0=b0[b0.protocol.eq(protocol)]
            if scope=='B0_all62_reference_ONLY':
                frame=source_b0[source_b0.reference.eq('B0_all_train')]
                keys=frame[['outer_fold','drug_id','class_id']].copy()
                panels=build_panels(keys,{},frame,ids,truth,'B0_all62_reference_ONLY',['B0_all_train'])
                # Only all-train is supplied; supplementary scope never compared to B1/B2.
                panels={'B0_all_train':panels['B0_all_train']}
            else:
                keys,baseline=scoped_reference_rows(predictions,protocol,scope,complete_ids)
                panels=build_panels(keys,baseline,source_b0,ids,truth,scope)
            boots={};points={}
            for model,panel in panels.items():
                base={'protocol':protocol,'scope':scope,'model':model,'semantics':SEMANTICS,'exploratory_after_baseline':True}
                point=panel.evaluate();points[model]={k:float(v[0]) for k,v in point.items()};boots[model]=panel.evaluate(weights)
                for metric in METRICS:
                    lo,hi,n,reason=percentile_interval(boots[model][metric],policy['bootstrap_min_valid'])
                    metric_rows.append({**base,'metric':metric,'estimate':points[model][metric],'CI95_low':lo,'CI95_high':hi,
                        'valid_bootstrap_replicates':n,'CI_NA_reason':reason,'CI_scope':policy['CI_scope']})
                for r in panel.drug_support:drug_rows.append({**base,**r,'outer_fold':folds[r['drug_id']],'structural_group':groups[r['drug_id']]})
                class_rows.extend({**base,**r} for r in panel.class_support())
                p=int(panel.y[panel.mask].sum());pairs=int(panel.mask.sum())
                total=sum(len([c for c,seen in truth.items() if d in seen]) for d,n in zip(ids,panel.mask.sum(axis=1)) if n)
                coverage.append({**base,'inventory_drugs':62,'scored_drugs':int(panel.mask.any(axis=1).sum()),
                    'drug_AP_evaluable':int(np.isfinite(panel.drug_AP).sum()),'scored_pairs':pairs,'observed_positive_scored':p,
                    'unknown_scored_NOT_verified_negative':pairs-p,'source_positive_for_scored_drugs':total,'out_of_scored_vocab_positive':total-p,
                    'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in panel.class_support())})
                for f in range(1,6):
                    idx=[i for i,d in enumerate(ids) if folds[d]==f];drug_ids=[ids[i] for i in idx]
                    fp=MetricPanel(panel.y[idx],panel.scores[idx],drug_ids,panel.classes)
                    for metric,value in fp.evaluate().items():fold_rows.append({**base,'outer_fold':f,'metric':metric,'estimate':float(value[0]),
                        'scored_drugs':int(fp.mask.any(axis=1).sum()),'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in fp.class_support())})
                if model.startswith('B0') and scope!='B0_all62_reference_ONLY':
                    ii,jj=np.where(panel.mask)
                    raw_scores.extend({**base,'outer_fold':folds[ids[i]],'drug_id':ids[i],'class_id':panel.classes[j],
                        'observed_record_s':int(panel.y[i,j]),'frequency_score':panel.scores[i,j]} for i,j in zip(ii,jj))
            if scope!='B0_all62_reference_ONLY':
                comparisons=[]
                for model in ('B1','B2'):
                    if model not in panels:continue
                    comparisons.extend([(model,'B0_like_'+model),(model,'B0_all_train')])
                if 'B1' in panels and 'B2' in panels:comparisons.append(('B2','B1'))
                for first,second in comparisons:
                    for metric in METRICS:
                        lo,hi,n,reason=percentile_interval(boots[first][metric]-boots[second][metric],policy['bootstrap_min_valid'])
                        deltas.append({'protocol':protocol,'scope':scope,'first':first,'reference':second,'metric':metric,
                            'first_minus_reference':points[first][metric]-points[second][metric],
                            'CI95_low':lo,'CI95_high':hi,'valid_bootstrap_replicates':n,'CI_NA_reason':reason,
                            'semantics':SEMANTICS,'CI_scope':policy['CI_scope'],'exploratory_after_baseline':True})
            print(f'Exploratory B0 paired evaluation completed: {protocol} / {scope}',flush=True)
    for name,rows in [('metrics_with_group_CI.csv',metric_rows),('paired_differences_group_CI.csv',deltas),
        ('per_drug_metrics.csv',drug_rows),('per_class_metrics.csv',class_rows),('within_outer_fold_metrics.csv',fold_rows),
        ('coverage_and_positive_unknown.csv',coverage),('B0_matched_scores.csv',raw_scores)]:write_csv(QA/name,pd.DataFrame(rows))
    if sha(QA/'train_frequency_estimates.csv')!=frequency_hash or sha(QA/'B0_outer_query_scores.csv')!=query_hash:raise RuntimeError('B0 estimator changed during evaluation')
    check_preservation()
    write_json(QA/'evaluation_complete.json',{'version':policy['version'],'policy_sha256':sha(QA/'policy_before_B0_results.json'),
        'frequency_sha256_unchanged':frequency_hash,'query_scores_sha256_unchanged':query_hash,
        'B1_B2_score_file_sha256_unchanged':sha(BASE/'oof_predictions.csv'),'selected_C_sha256_unchanged':sha(BASE/'selected_C.csv'),
        'group_bootstrap_reps':1000,'elapsed_seconds':time.perf_counter()-start,'semantics':SEMANTICS,
        'exploratory_after_B1_B2_results':True,'no_B1_B2_refit_or_retuning':True,'WP08_closed':False,'WP09_started':False})
    print('B0 evaluation complete. B1/B2 untouched; exploratory comparison only.',flush=True)


if __name__=='__main__':main()
