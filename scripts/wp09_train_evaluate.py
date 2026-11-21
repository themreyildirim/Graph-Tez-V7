"""Sabit OOF PPI ablation + WP08 referansları; fit/seed/eşik seçimi yapmaz."""
import json,time
import numpy as np
import pandas as pd
from wp09_train import ROOT,QA,PREP,SEMANTICS,NAMES,sha,write_json,csv,preserve,source_labels
from wp08_baseline_metrics import MetricPanel,grouped_bootstrap_weights,percentile_interval,mean_or_na

OLD=ROOT/'reports/qa/WP08/baseline_v1'
B0=ROOT/'reports/qa/WP08/B0_frequency_reference_v1'
MEAN='G_shuffledPPI_mean3_metrics'


def shared_keys(expected,new,protocol):
    keys=['outer_fold','drug_id','class_id'];current=expected[keys].drop_duplicates()
    for model in NAMES:
        f=new[new.protocol.eq(protocol)&new.model.eq(model)]
        f=f[np.isfinite(f.score_observed_record_proxy)]
        current=current.merge(f[keys],on=keys,how='inner',validate='one_to_one')
    excluded=expected[keys].merge(current,on=keys,how='left',indicator=True)
    excluded=excluded[excluded._merge.eq('left_only')].drop(columns='_merge')
    return current,excluded


def make_panel(frame,keys,ids,truth,score_column):
    classes=sorted(keys.class_id.unique());ci={c:j for j,c in enumerate(classes)};di={d:i for i,d in enumerate(ids)}
    y=np.asarray([[int(c in truth[d]) for c in classes] for d in ids],dtype=np.int8).reshape(len(ids),len(classes))
    scores=np.full(y.shape,np.nan)
    matched=keys.merge(frame[['outer_fold','drug_id','class_id',score_column]],on=['outer_fold','drug_id','class_id'],how='left',validate='one_to_one')
    if matched[score_column].isna().any():raise ValueError('Unmatched score in fixed comparison keys')
    for row in matched.itertuples():scores[di[row.drug_id],ci[row.class_id]]=getattr(row,score_column)
    return MetricPanel(y,scores,ids,classes)


def bootstrap_primary(panel,weights):
    valid=np.isfinite(panel.drug_AP);denominator=weights@valid.astype(float)
    drug_ap=np.divide(weights@np.where(valid,panel.drug_AP,0.),denominator,out=np.full(len(weights),np.nan),where=denominator>0)
    ap=[];auc=[]
    for start in range(0,len(weights),16):
        a,u=panel.micro.evaluate(weights[start:start+16]);ap.append(a);auc.append(u)
    return {'drug_macro_AP':drug_ap,'micro_AP':np.concatenate(ap),'micro_AUROC':np.concatenate(auc)}


def strict_mean3(values):
    array=np.asarray(values,dtype=float)
    if array.shape[0]!=3:raise ValueError('Exactly three fixed null replicas required')
    return np.mean(array,axis=0)  # A missing replica stays NA; nanmean/best-of are prohibited.


def main():
    preserve()
    if not (QA/'scoring_complete.json').exists():raise RuntimeError('Frozen outer scores required')
    if (QA/'evaluation_complete.json').exists():raise RuntimeError('Evaluation v1 already completed; no result-driven changes')
    started=time.perf_counter();run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
    new=pd.read_csv(QA/'oof_predictions.csv');old=pd.read_csv(OLD/'oof_predictions.csv');old=old[old.family.eq('PT')]
    frequency=pd.read_csv(B0/'B0_outer_query_scores.csv').rename(columns={'pt_cui':'class_id'})
    source=source_labels();truth={d:set(f.class_id) for d,f in source.groupby('drug_id')}
    membership=pd.read_csv(PREP/'outer_membership_v1.csv')
    metric_rows=[];differences=[];perdrug=[];perclass=[];fold_rows=[];coverage=[];key_rows=[];excluded_rows=[]
    bootstrap_parts=[]
    for pi,protocol in enumerate(('primary','stress')):
        members=membership[membership.protocol.eq(protocol)].sort_values('drug_id');ids=list(members.drug_id)
        fold_map=dict(zip(members.drug_id,members.outer_test_fold));groups=dict(zip(members.drug_id,members.group_id))
        weights=grouped_bootstrap_weights(ids,groups,1000,20261106+9000+pi)
        for scope in ('paired54','own61'):
            b1=old[old.protocol.eq(protocol)&old.model.eq('B1')];b2=old[old.protocol.eq(protocol)&old.model.eq('B2')]
            expected=b2[['outer_fold','drug_id','class_id']]
            if scope=='paired54':expected=expected.merge(b1[['outer_fold','drug_id','class_id']],on=['outer_fold','drug_id','class_id'],validate='one_to_one')
            keys,excluded=shared_keys(expected,new,protocol)
            key_rows.extend(keys.assign(protocol=protocol,scope=scope).to_dict('records'))
            excluded_rows.extend(excluded.assign(protocol=protocol,scope=scope,reason='missing/nonfinite new-model score; shared mask for all models').to_dict('records'))
            frames={'B2':(b2,'score_observed_record_proxy')}
            if scope=='paired54':frames['B1']=(b1,'score_observed_record_proxy')
            refs=['B0_all_train','B0_like_B2']+(['B0_like_B1'] if scope=='paired54' else [])
            for ref in refs:frames[ref]=(frequency[frequency.protocol.eq(protocol)&frequency.reference.eq(ref)],'frequency_score')
            for name in NAMES:frames[name]=(new[new.protocol.eq(protocol)&new.model.eq(name)],'score_observed_record_proxy')
            panels={name:make_panel(frame,keys,ids,truth,column) for name,(frame,column) in frames.items()}
            first=next(iter(panels.values())).mask
            assert all(np.array_equal(first,p.mask) for p in panels.values())
            points={};boots={};fold_values={}
            for name,panel in panels.items():
                base={'protocol':protocol,'scope':scope,'model':name,'semantics':SEMANTICS}
                points[name]={k:float(v[0]) for k,v in panel.evaluate().items()}
                boots[name]=bootstrap_primary(panel,weights)
                class_rows=panel.class_support();perclass.extend({**base,**r} for r in class_rows)
                perdrug.extend({**base,**r,'outer_fold':fold_map[r['drug_id']],'structural_group':groups[r['drug_id']]} for r in panel.drug_support)
                scored_drugs=[d for d,n in zip(ids,panel.mask.sum(axis=1)) if n]
                positives=int(panel.y[panel.mask].sum());pairs=int(panel.mask.sum())
                source_positive=sum(len(truth[d]) for d in scored_drugs)
                coverage.append({**base,'inventory_drugs':62,'expected_comparison_drugs':expected.drug_id.nunique(),
                    'scored_drugs':len(scored_drugs),'AP_evaluable_drugs':int(np.isfinite(panel.drug_AP).sum()),
                    'expected_scored_pairs':len(expected),'scored_pairs':pairs,'excluded_comparison_keys':len(excluded),
                    'observed_positive_scored':positives,'unknown_NOT_verified_negative':pairs-positives,
                    'source_positive_for_scored_drugs':source_positive,'out_of_scored_vocab_positive':source_positive-positives,
                    'scored_class_union':len(panel.classes),'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in class_rows),
                    'class_AUROC_NA':sum(not np.isfinite(r['AUROC']) for r in class_rows)})
                local_values=[]
                for fold in range(1,6):
                    idx=[i for i,d in enumerate(ids) if fold_map[d]==fold]
                    fp=MetricPanel(panel.y[idx],panel.scores[idx],[ids[i] for i in idx],panel.classes)
                    value={k:float(v[0]) for k,v in fp.evaluate().items()};local_values.append(value['class_macro_AUROC'])
                    for metric,estimate in value.items():fold_rows.append({**base,'outer_fold':fold,'metric':metric,'estimate':estimate,
                        'scored_drugs':int(fp.mask.any(axis=1).sum()),'drug_AP_evaluable':int(np.isfinite(fp.drug_AP).sum()),
                        'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in fp.class_support()),
                        'CI_status':'descriptive within-fold; folds not independent repeats'})
                fold_values[name]=np.asarray(local_values)
                points[name]['within_fold_class_macro_AUROC']=float(mean_or_na(local_values))
                for metric,estimate in points[name].items():
                    if metric in boots[name]:lo,hi,n,reason=percentile_interval(boots[name][metric],800)
                    else:lo=hi=None;n=0;reason='descriptive_class_metric_no_independent_fold_CI'
                    metric_rows.append({**base,'metric':metric,'estimate':estimate,'CI95_low':lo,'CI95_high':hi,
                        'valid_bootstrap_replicates':n,'CI_NA_reason':reason,
                        'CI_scope':'paired structural groups, fixed OOF conditional; not full retraining/external validation',
                        'interpretation':'pooled diagnostic only' if metric=='class_macro_AUROC' else 'within-fold descriptive mean' if metric.startswith('within_') else 'observed-record ranking'})
            replicas=[f'G_shuffledPPI_R{r}' for r in range(3)]
            points[MEAN]={metric:float(strict_mean3([points[r][metric] for r in replicas])) for metric in points[replicas[0]]}
            boots[MEAN]={metric:strict_mean3([boots[r][metric] for r in replicas]) for metric in boots[replicas[0]]}
            for metric,estimate in points[MEAN].items():
                if metric in boots[MEAN]:lo,hi,n,reason=percentile_interval(boots[MEAN][metric],800)
                else:lo=hi=None;n=0;reason='descriptive_class_metric_no_independent_fold_CI'
                metric_rows.append({'protocol':protocol,'scope':scope,'model':MEAN,'semantics':SEMANTICS,'metric':metric,'estimate':estimate,
                    'CI95_low':lo,'CI95_high':hi,'valid_bootstrap_replicates':n,'CI_NA_reason':reason,
                    'CI_scope':'mean of three metrics on each shared group draw; no prediction ensemble',
                    'interpretation':'equal mean of fixed3 replica metrics; not best replica'})
            for fold in range(1,6):
                for metric in points[replicas[0]]:
                    if metric.startswith('within_'):continue
                    values=[r['estimate'] for r in fold_rows if r['protocol']==protocol and r['scope']==scope and r['outer_fold']==fold and r['metric']==metric and r['model'] in replicas]
                    fold_rows.append({'protocol':protocol,'scope':scope,'model':MEAN,'semantics':SEMANTICS,'outer_fold':fold,
                        'metric':metric,'estimate':float(strict_mean3(values)),'CI_status':'equal mean of replica metrics, no prediction ensemble'})
            comparisons=[('G_realPPI','G_noPPI'),('G_realPPI',MEAN),('G_noPPI','B2'),('G_realPPI','B2'),('G_realPPI','B0_like_B2'),
                (MEAN,'B2'),('G_noPPI','B0_like_B2')]
            if scope=='paired54':comparisons.extend([('G_realPPI','B1'),('G_noPPI','B1')])
            for first_name,ref in comparisons:
                for metric in ('drug_macro_AP','micro_AP','micro_AUROC'):
                    lo,hi,n,reason=percentile_interval(boots[first_name][metric]-boots[ref][metric],800)
                    differences.append({'protocol':protocol,'scope':scope,'first':first_name,'reference':ref,'metric':metric,
                        'first_minus_reference':points[first_name][metric]-points[ref][metric],'CI95_low':lo,'CI95_high':hi,
                        'valid_bootstrap_replicates':n,'CI_NA_reason':reason,'semantics':SEMANTICS,
                        'CI_scope':'paired fixed OOF structural-group conditional; replicas not independent sample units'})
            for name,samples in boots.items():
                for metric,values in samples.items():bootstrap_parts.append({'protocol':protocol,'scope':scope,'model':name,'metric':metric,'valid_replicates':int(np.isfinite(values).sum())})
            print(f'WP09 paired evaluation: {protocol}/{scope}; {len(keys)}/{len(expected)} frozen keys',flush=True)
    for name,data in [('metrics_with_group_CI.csv',metric_rows),('paired_differences_group_CI.csv',differences),
        ('per_drug_metrics.csv',perdrug),('per_class_metrics.csv',perclass),('outer_fold_metrics.csv',fold_rows),
        ('evaluation_coverage.csv',coverage),('comparison_keys.csv',key_rows),('excluded_comparison_keys.csv',excluded_rows),
        ('bootstrap_validity.csv',bootstrap_parts)]:
        frame=pd.DataFrame(data)
        if name=='excluded_comparison_keys.csv' and frame.empty:frame=pd.DataFrame(columns=['outer_fold','drug_id','class_id','protocol','scope','reason'])
        csv(name,frame)
    write_json(QA/'evaluation_complete.json',{'elapsed_seconds':time.perf_counter()-started,'bootstrap_reps':1000,
        'OOF_predictions_sha256':sha(QA/'oof_predictions.csv'),'selection_commit_sha256':sha(QA/'selection_complete_before_test_scoring.json'),
        'WP08_scores_sha256_unchanged':sha(OLD/'oof_predictions.csv'),'WP08_C_sha256_unchanged':sha(OLD/'selected_C.csv'),
        'refit_or_retuning':False,'no_prediction_ensemble':True,'prior_files_verified':preserve(),'semantics':SEMANTICS,'WP10':False})


if __name__=='__main__':main()
