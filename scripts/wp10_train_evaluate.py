"""Dondurulmuş OOF skorlarında aynı kapsam ve eşleştirilmiş factorial kontrastlar."""
import json,time
import numpy as np
import pandas as pd
from wp10_train import ROOT,QA,PREP,NAMES,SEMANTICS,sha,write_json,csv,preserve,source_labels
from wp09_train_evaluate import make_panel,bootstrap_primary
from wp08_baseline_metrics import MetricPanel,grouped_bootstrap_weights,percentile_interval,mean_or_na


def main():
    preserve()
    if not (QA/'scoring_complete.json').exists():raise RuntimeError('Committed OOF scores required')
    if (QA/'evaluation_complete.json').exists():raise RuntimeError('Frozen evaluation already exists')
    started=time.perf_counter();run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
    new=pd.read_csv(QA/'oof_predictions.csv')
    old=pd.read_csv(ROOT/'reports/qa/WP08/baseline_v1/oof_predictions.csv');old=old[old.family.eq('PT')]
    freq=pd.read_csv(ROOT/'reports/qa/WP08/B0_frequency_reference_v1/B0_outer_query_scores.csv').rename(columns={'pt_cui':'class_id'})
    wp09=pd.read_csv(ROOT/'reports/qa/WP09/training_v1/oof_predictions.csv')
    source=source_labels();truth={d:set(f.class_id) for d,f in source.groupby('drug_id')}
    membership=pd.read_csv(PREP/'outer_membership_v1.csv')
    metrics=[];delta=[];factorial=[];perdrug=[];perclass=[];foldrows=[];coverage=[];keyrows=[];excludedrows=[];validity=[]
    for pi,protocol in enumerate(('primary','stress')):
        members=membership[membership.protocol.eq(protocol)].sort_values('drug_id');ids=list(members.drug_id)
        folds=dict(zip(members.drug_id,members.outer_test_fold));groups=dict(zip(members.drug_id,members.group_id))
        weights=grouped_bootstrap_weights(ids,groups,1000,20261106+9000+pi)
        for scope in ('paired54','own61'):
            b1=old[old.protocol.eq(protocol)&old.model.eq('B1')];b2=old[old.protocol.eq(protocol)&old.model.eq('B2')]
            columns=['outer_fold','drug_id','class_id'];expected=b2[columns]
            if scope=='paired54':expected=expected.merge(b1[columns],on=columns,validate='one_to_one')
            keys=expected.copy()
            for arm in NAMES:
                part=new[new.protocol.eq(protocol)&new.model.eq(arm)&np.isfinite(new.score_observed_record_proxy)]
                keys=keys.merge(part[columns],on=columns,validate='one_to_one')
            excluded=expected.merge(keys,on=columns,how='left',indicator=True)
            excluded=excluded[excluded._merge.eq('left_only')].drop(columns='_merge')
            keyrows.extend(keys.assign(protocol=protocol,scope=scope).to_dict('records'))
            excludedrows.extend(excluded.assign(protocol=protocol,scope=scope,reason='shared4 missing/nonfinite score').to_dict('records'))
            frames={'B2':(b2,'score_observed_record_proxy')}
            if scope=='paired54':frames['B1']=(b1,'score_observed_record_proxy')
            for ref in ['B0_all_train','B0_like_B2']+(['B0_like_B1'] if scope=='paired54' else []):frames[ref]=(freq[freq.protocol.eq(protocol)&freq.reference.eq(ref)],'frequency_score')
            for ref in ['G_noPPI','G_realPPI']:frames['WP09_'+ref]=(wp09[wp09.protocol.eq(protocol)&wp09.model.eq(ref)],'score_observed_record_proxy')
            for arm in NAMES:frames[arm]=(new[new.protocol.eq(protocol)&new.model.eq(arm)],'score_observed_record_proxy')
            panels={name:make_panel(f,keys,ids,truth,c) for name,(f,c) in frames.items()}
            mask=next(iter(panels.values())).mask;assert all(np.array_equal(mask,p.mask) for p in panels.values())
            points={};boots={}
            for name,p in panels.items():
                base={'protocol':protocol,'scope':scope,'model':name,'semantics':SEMANTICS}
                points[name]={k:float(v[0]) for k,v in p.evaluate().items()};boots[name]=bootstrap_primary(p,weights)
                classrows=p.class_support();perclass.extend({**base,**r} for r in classrows)
                perdrug.extend({**base,**r,'outer_fold':folds[r['drug_id']],'structural_group':groups[r['drug_id']]} for r in p.drug_support)
                scored=[d for d,n in zip(ids,p.mask.sum(1)) if n];pos=int(p.y[p.mask].sum());pairs=int(p.mask.sum())
                srcpos=sum(len(truth[d]) for d in scored)
                coverage.append({**base,'inventory_drugs':62,'scored_drugs':len(scored),'AP_evaluable_drugs':int(np.isfinite(p.drug_AP).sum()),
                    'expected_scored_pairs':len(expected),'scored_pairs':pairs,'excluded_comparison_keys':len(excluded),
                    'observed_positive_scored':pos,'unknown_NOT_verified_negative':pairs-pos,'source_positive_for_scored_drugs':srcpos,
                    'out_of_scored_vocab_positive':srcpos-pos,'scored_class_union':len(p.classes),
                    'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in classrows),'class_AUROC_NA':sum(not np.isfinite(r['AUROC']) for r in classrows)})
                within=[]
                for fold in range(1,6):
                    idx=[i for i,d in enumerate(ids) if folds[d]==fold]
                    fp=MetricPanel(p.y[idx],p.scores[idx],[ids[i] for i in idx],p.classes)
                    local={k:float(v[0]) for k,v in fp.evaluate().items()};within.append(local['class_macro_AUROC'])
                    for metric,value in local.items():foldrows.append({**base,'outer_fold':fold,'metric':metric,'estimate':value,
                        'scored_drugs':int(fp.mask.any(1).sum()),'class_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in fp.class_support()),'CI_status':'descriptive;folds not independent'})
                points[name]['within_fold_class_macro_AUROC']=float(mean_or_na(within))
                for metric,value in points[name].items():
                    if metric in boots[name]:lo,hi,n,reason=percentile_interval(boots[name][metric],800)
                    else:lo=hi=None;n=0;reason='descriptive class metric;no independent-fold CI'
                    metrics.append({**base,'metric':metric,'estimate':value,'CI95_low':lo,'CI95_high':hi,'valid_bootstrap_replicates':n,
                        'CI_NA_reason':reason,'interpretation':'pooled diagnostic only' if metric=='class_macro_AUROC' else 'within-fold descriptive mean' if metric.startswith('within_') else 'observed-record ranking',
                        'CI_scope':'paired structural groups;fixed OOF conditional;not retraining/external validation'})
                for metric,values in boots[name].items():validity.append({**base,'metric':metric,'valid_replicates':int(np.isfinite(values).sum())})
            for contrast,coeff in run['evaluation_before_results']['contrasts'].items():
                for metric in ['drug_macro_AP','micro_AP','micro_AUROC']:
                    value=sum(c*points[name][metric] for name,c in coeff.items())
                    samples=sum(c*boots[name][metric] for name,c in coeff.items());lo,hi,n,reason=percentile_interval(samples,800)
                    factorial.append({'protocol':protocol,'scope':scope,'contrast':contrast,'metric':metric,'estimate':value,'CI95_low':lo,'CI95_high':hi,
                        'valid_bootstrap_replicates':n,'CI_NA_reason':reason,'coefficients':json.dumps(coeff),'semantics':SEMANTICS,
                        'interpretation':'difference of observed-record metrics;not biological causality','CI_scope':'paired fixed-OOF structural-group conditional'})
            for arm in NAMES:
                for ref in ['B2','B0_like_B2','WP09_G_noPPI','WP09_G_realPPI']+(['B1'] if scope=='paired54' else []):
                    for metric in ['drug_macro_AP','micro_AP','micro_AUROC']:
                        lo,hi,n,reason=percentile_interval(boots[arm][metric]-boots[ref][metric],800)
                        delta.append({'protocol':protocol,'scope':scope,'first':arm,'reference':ref,'metric':metric,'first_minus_reference':points[arm][metric]-points[ref][metric],
                            'CI95_low':lo,'CI95_high':hi,'valid_bootstrap_replicates':n,'CI_NA_reason':reason,'semantics':SEMANTICS})
            print(f'WP10 evaluation {protocol}/{scope}: {len(keys)}/{len(expected)} shared keys',flush=True)
    outputs={'metrics_with_group_CI.csv':metrics,'paired_reference_differences.csv':delta,'factorial_contrasts_group_CI.csv':factorial,
        'per_drug_metrics.csv':perdrug,'per_class_metrics.csv':perclass,'outer_fold_metrics.csv':foldrows,'evaluation_coverage.csv':coverage,
        'comparison_keys.csv':keyrows,'excluded_comparison_keys.csv':excludedrows,'bootstrap_validity.csv':validity}
    for name,rows in outputs.items():
        frame=pd.DataFrame(rows)
        if name=='excluded_comparison_keys.csv' and frame.empty:frame=pd.DataFrame(columns=['outer_fold','drug_id','class_id','protocol','scope','reason'])
        csv(name,frame)
    write_json(QA/'evaluation_complete.json',{'seconds':time.perf_counter()-started,'bootstrap_replicates':1000,'no_refit':True,
        'OOF_sha256':sha(QA/'oof_predictions.csv'),'prior_files_verified':preserve(),'WP11':False,'shuffled_PPI_experiments':False,'semantics':SEMANTICS})


if __name__=='__main__':main()
