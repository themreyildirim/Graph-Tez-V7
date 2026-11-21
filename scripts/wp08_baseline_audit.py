"""Baseline sonuçları için kapsam/NA ve provenans ekleri; yeniden fit yok."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import scipy,sklearn,platform
from wp08_baseline_train import ROOT,PREP,QA,MODEL,SEMANTICS,write_csv,write_json,sha


def main():
    parts=pd.read_csv(PREP/'nested_partitions_v1.csv');outer=pd.read_csv(PREP/'outer_membership_v1.csv')
    eligible=pd.read_csv(PREP/'prediction_eligibility.csv');fits=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'))
    rows=[]
    for path in sorted(MODEL.glob('*.json')):
        md=json.loads(path.read_text(encoding='utf-8'));context=md['context'];model=md['baseline']
        sub=parts[parts.context.eq(context)];train=set(sub[sub.split.eq('train')].drug_id)
        allowed=set(eligible[eligible.model.eq(model)&eligible.eligible].drug_id)
        if set(md['train_drug_ids'])!=train&allowed:raise RuntimeError('Classifier fit identity leakage')
        if md['transform_fit_sources']!=fits[context]:raise RuntimeError('Preprocessor scope changed')
        if sha(ROOT/md['parameters_file'])!=md['parameters_sha256']:raise RuntimeError('Model weights altered')
        rows.append({'context':context,'phase':md['phase'],'family':md['family'],'model':model,'C':md['C'],
            'model_fit_drugs':len(md['train_drug_ids']),'chemical_fit_drugs':len(fits[context]['chemistry_fit_drug_ids']),
            'protein_fit_accessions':len(fits[context]['protein_fit_accessions']),'fitted_classes':len(md['fitted_classes']),
            'parameter_file':md['parameters_file'],'parameters_sha256':md['parameters_sha256'],
            'test_drugs_in_fit':0,'seed':md['seed'],'semantics':SEMANTICS})
    write_csv(QA/'model_fit_provenance.csv',pd.DataFrame(rows))
    context=pd.read_csv(PREP/'context_summary.csv');context['semantics']=SEMANTICS
    write_csv(QA/'fold_train_validation_test_scope.csv',context)
    folds=pd.read_csv(QA/'outer_fold_metrics.csv')
    folds['CI95_low']=np.nan;folds['CI95_high']=np.nan
    folds['CI_NA_reason']='Per-fold CI not estimated; overlapping fitted folds are not independent; group-resampled OOF CI reported separately'
    write_csv(QA/'outer_fold_metrics.csv',folds)
    classes=pd.read_csv(QA/'per_class_metrics.csv')
    classes['CI_status']='No per-class CI; sparse ragged support; aggregate conditional group-bootstrap CI reported separately'
    write_csv(QA/'per_class_metrics.csv',classes)
    # Seçilmemiş/fit edilememiş pozitif kapsamı da her fold/model için açıklanır.
    prep_eval=pd.read_csv(PREP/'metric_evaluability_NO_scores.csv')
    pt_scope=prep_eval[prep_eval.context.str.endswith('final')&prep_eval.split.eq('test')].copy()
    pt_scope['semantics']=SEMANTICS;write_csv(QA/'PT_target_scope_and_unobserved_support.csv',pt_scope)
    trace=pd.read_csv(QA/'class_fit_trace.csv');write_csv(QA/'fit_status_summary.csv',trace.groupby(['phase','family','model','status']).size().rename('candidate_class_fits').reset_index().assign(semantics=SEMANTICS))
    write_json(QA/'environment.json',{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
        'sklearn':sklearn.__version__,'threadpool_limit':1,'new_packages_installed':False,'model_version':'WP08-observed-record-L2LR-v1',
        'semantics':SEMANTICS})
    write_json(QA/'model_artifact_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(MODEL.iterdir()) if p.is_file()})
    print('Model/fit identity audit passed:',len(rows),'bundles; no refitting')


if __name__=='__main__':main()
