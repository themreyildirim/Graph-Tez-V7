"""Sabit outer OOF tahminlerinin kapsam/paired analizi; refit veya ayar yok."""
from pathlib import Path
import json,time,hashlib
import numpy as np
import pandas as pd
from wp08_baseline_train import ROOT,PREP,QA,MODEL,CONFIG,SEED,load_labels,positive_lookup,proxy_matrix,write_json,write_csv,sha
from wp08_baseline_metrics import MetricPanel,METRICS,SEMANTICS,grouped_bootstrap_weights,percentile_interval


def make_panels(protocol,family,predictions,outer_membership,eligibility,vocabs,historical,scope):
    membership=outer_membership[outer_membership.protocol.eq(protocol)].sort_values('drug_id')
    ids=list(membership.drug_id);fold=dict(zip(membership.drug_id,membership.outer_test_fold))
    allowed={m:set(eligibility[eligibility.model.eq(m)&eligibility.eligible].drug_id) for m in ('B1','B2')}
    shared=allowed['B1']&allowed['B2']
    masks=pd.read_csv(PREP/'complete_case_53_inventory_ONLY.csv')
    complete=set(masks[masks.complete_case_sensitivity].drug_id)
    model_frames={m:predictions[predictions.protocol.eq(protocol)&predictions.family.eq(family)&predictions.model.eq(m)] for m in ('B1','B2')}
    class_by_fold={m:{} for m in ('B1','B2')}
    # Targets common across models are based on successful TRAIN fits, never test outcomes.
    for f in range(1,6):
        candidates={m:set(json.loads((MODEL/f'{protocol}_o{f:02}_final_{family}_{m}_selected.json').read_text(encoding='utf-8'))['fitted_classes']) for m in ('B1','B2')}
        if scope!='own':
            common=candidates['B1']&candidates['B2']
            for m in class_by_fold:class_by_fold[m][f]=common
        else:
            for m in class_by_fold:class_by_fold[m][f]=candidates[m]
    rows={d:i for i,d in enumerate(ids)}
    lookup=positive_lookup(load_labels()[family])
    panels={}
    for model in ('B1','B2'):
        universe=sorted(set.union(*class_by_fold[model].values()))
        cols={c:j for j,c in enumerate(universe)};y=proxy_matrix(ids,universe,lookup)
        scores=np.full((len(ids),len(universe)),np.nan)
        valid=allowed[model] if scope=='own' else shared if scope=='paired54' else complete
        for row in model_frames[model].itertuples():
            if row.drug_id in valid and row.class_id in class_by_fold[model][row.outer_fold]:scores[rows[row.drug_id],cols[row.class_id]]=row.score_observed_record_proxy
        panels[model]=MetricPanel(y,scores,ids,universe)
    if scope!='own':
        # Fit failure in one model causes paired score to be excluded in BOTH.
        both=np.isfinite(panels['B1'].scores)&np.isfinite(panels['B2'].scores)
        panels={m:MetricPanel(p.y,np.where(both,p.scores,np.nan),ids,p.classes) for m,p in panels.items()}
    return panels,dict(zip(membership.drug_id,membership.group_id))


def main():
    complete=json.loads((QA/'training_complete.json').read_text(encoding='utf-8'))
    selected_sha=sha(QA/'selected_C.csv')
    if selected_sha!=complete['selected_C_sha256']:raise RuntimeError('Selection changed after training')
    frozen=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
    run_inputs=json.loads((QA/'preparation_input_manifest.json').read_text(encoding='utf-8'))
    if any(sha(ROOT/p)!=h for p,h in run_inputs.items()):raise RuntimeError('Frozen preparation input changed')
    pred=pd.read_csv(QA/'oof_predictions.csv');membership=pd.read_csv(PREP/'outer_membership_v1.csv')
    eligibility=pd.read_csv(PREP/'prediction_eligibility.csv')
    vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'));hist=json.loads((PREP/'historical30_reference.json').read_text(encoding='utf-8'))['classes']
    metrics=[];fold_metrics=[];drug_rows=[];class_rows=[];paired_diffs=[];coverage=[];bootstrap_summary=[]
    all_labels=load_labels();start=time.perf_counter()
    for pi,protocol in enumerate(('primary','stress')):
        for family in ('PT','historical30'):
            for scope in ('own','paired54','complete_case53'):
                panels,groups=make_panels(protocol,family,pred,membership,eligibility,vocab,hist,scope)
                weights=grouped_bootstrap_weights(panels['B1'].ids,groups,frozen['bootstrap_reps'],SEED+9000+pi)
                boots={};points={}
                for model,panel in panels.items():
                    points[model]={k:float(v[0]) for k,v in panel.evaluate().items()}
                    boots[model]=panel.evaluate(weights)
                    base={'protocol':protocol,'family':family,'scope':scope,'model':model,'semantics':SEMANTICS}
                    for metric in METRICS:
                        lo,hi,valid,reason=percentile_interval(boots[model][metric],frozen['bootstrap_min_valid'])
                        metrics.append({**base,'metric':metric,'estimate':points[model][metric],'CI95_low':lo,'CI95_high':hi,
                            'valid_bootstrap_replicates':valid,'CI_NA_reason':reason,
                            'CI_interpretation':frozen['CI_scope']})
                    membership_here=membership[membership.protocol.eq(protocol)].set_index('drug_id')
                    for row in panel.drug_support:
                        drug_rows.append({**base,**row,'outer_fold':int(membership_here.loc[row['drug_id'],'outer_test_fold']),
                            'structural_group':groups[row['drug_id']]})
                    supports=panel.class_support()
                    for row in supports:class_rows.append({**base,**row})
                    source_total=len(all_labels[family][all_labels[family].drug_id.isin([d for d,n in zip(panel.ids,panel.mask.sum(axis=1)) if n>0])])
                    observed_scored=int(panel.y[panel.mask].sum());scored=int(panel.mask.sum())
                    coverage.append({**base,'cohort_drugs':len(panel.ids),'input_scope_name':scope,
                        'scored_drugs':int(panel.mask.any(axis=1).sum()),'drug_AP_evaluable':int(np.isfinite(panel.drug_AP).sum()),
                        'drug_AP_NA':int((~np.isfinite(panel.drug_AP)).sum()),'scored_pairs':scored,
                        'observed_positive_scored':observed_scored,'unknown_scored_NOT_verified_negative':scored-observed_scored,
                        'source_positive_for_scored_drugs':source_total,'out_of_scored_vocab_positive':source_total-observed_scored,
                        'classes_with_any_score':int(panel.mask.any(axis=0).sum()),
                        'class_AP_AUROC_evaluable':sum(np.isfinite(r['AUROC']) for r in supports),
                        'class_metric_NA':sum(not np.isfinite(r['AUROC']) for r in supports)})
                    for f in range(1,6):
                        ids=[d for d in panel.ids if membership_here.loc[d,'outer_test_fold']==f]
                        indices=[panel.ids.index(d) for d in ids]
                        fold=MetricPanel(panel.y[indices],panel.scores[indices],ids,panel.classes)
                        for metric,value in fold.evaluate().items():
                            fold_metrics.append({**base,'outer_fold':f,'metric':metric,'estimate':float(value[0]),
                                'scored_drugs':int(fold.mask.any(axis=1).sum()),'drug_AP_evaluable':int(np.isfinite(fold.drug_AP).sum()),
                                'scored_pairs':int(fold.mask.sum()),'observed_positive_scored':int(fold.y[fold.mask].sum())})
                if scope!='own':
                    for metric in METRICS:
                        delta=boots['B2'][metric]-boots['B1'][metric]
                        lo,hi,valid,reason=percentile_interval(delta,frozen['bootstrap_min_valid'])
                        paired_diffs.append({'protocol':protocol,'family':family,'scope':scope,'metric':metric,
                            'B2_minus_B1':points['B2'][metric]-points['B1'][metric],'CI95_low':lo,'CI95_high':hi,
                            'valid_bootstrap_replicates':valid,'CI_NA_reason':reason,'semantics':SEMANTICS,
                            'CI_interpretation':frozen['CI_scope']})
                bootstrap_summary.append({'protocol':protocol,'family':family,'scope':scope,'seed':SEED+9000+pi,
                    'reps':len(weights),'unique_groups':len(set(groups.values())),'unit':'structural group including all members',
                    'draws_shared_across_B1_B2':True,'full_training_refit_bootstrap':False,'semantics':SEMANTICS})
                print(f'OOF/group-bootstrap evaluated: {protocol} {family} {scope}',flush=True)
    for name,rows in [('oof_metrics_with_group_CI.csv',metrics),('outer_fold_metrics.csv',fold_metrics),
        ('per_drug_metrics.csv',drug_rows),('per_class_metrics.csv',class_rows),('paired_B2_minus_B1_group_CI.csv',paired_diffs),
        ('evaluation_coverage.csv',coverage),('bootstrap_design.csv',bootstrap_summary)]:write_csv(QA/name,pd.DataFrame(rows))
    write_json(QA/'evaluation_complete.json',{'selected_C_sha256_unchanged':selected_sha,'OOF_predictions_sha256':sha(QA/'oof_predictions.csv'),
        'metrics':METRICS,'bootstrap_replicates':frozen['bootstrap_reps'],'CI_scope':frozen['CI_scope'],
        'semantics':SEMANTICS,'elapsed_seconds':time.perf_counter()-start,'WP09_started':False,
        'test_information_used_for_selection':False,'complete_case_sensitivity':'evaluation subset of same fitted models, not retrained complete-case models'})
    print('Evaluation complete. No model/feature/seed refit or protocol change.',flush=True)


if __name__=='__main__':main()
