"""Onaylı ilk WP08 LR: kilitli hazırlık girdileri salt okunur kullanılır.

Binary s=observed record proxy. Unknown bilimsel negatif değildir. Önce bütün
inner seçimler, sonra outer fit ve yalnız son aşamada test skor değerlendirmesi.
"""
from pathlib import Path
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
import json,hashlib,sys,warnings,time
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from scipy.special import expit
from threadpoolctl import threadpool_limits
from wp08_baseline_metrics import MetricPanel,SEMANTICS,mean_or_na

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'reports/qa/WP08/experimental_preparation';QA=ROOT/'reports/qa/WP08/baseline_v1'
MODEL=ROOT/'models/WP08_baseline_v1';GRID=(.1,1.,10.);SEED=20261106
VERSION='WP08-observed-record-L2LR-v1'
CONFIG={'version':VERSION,'status':'USER_AUTHORIZED_FIRST_BASELINE','C_grid':GRID,'seed':SEED,
    'solver':'liblinear','l1_ratio':0.0,'class_weight':None,'tol':1e-8,'max_iter':10000,
    'fit_intercept':True,'intercept_scaling':1.0,'regularization':'L2; liblinear synthetic intercept regularized',
    'selection':'unweighted mean of valid inner fold drug-macro AP; C-independent scope per fold; tie tolerance 1e-12, smaller C',
    'inner_target_policy':'C-independent intersection of successful candidate fits within a fold; all exclusions logged',
    'outer_selection_uses_test':False,'bootstrap_reps':1000,'bootstrap_min_valid':800,
    'bootstrap_seed':'20261106 + 9000 + protocol_index','bootstrap_unit':'locked structural group; paired same draws',
    'CI_scope':'conditional fixed OOF prediction resampling; not full retraining or external validation uncertainty',
    'semantics':SEMANTICS,'ATC':False,'RF_MLP':False,'PPI':False,'context80':False,'WP09':False}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,x):
    def clean(v):
        if isinstance(v,dict):return {str(k):clean(a) for k,a in v.items()}
        if isinstance(v,(tuple,list)):return [clean(a) for a in v]
        if isinstance(v,np.generic):return clean(v.item())
        if isinstance(v,float) and not np.isfinite(v):return None
        return v
    p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def write_csv(p,f):f.to_csv(p,index=False,encoding='utf-8-sig',lineterminator='\n')


def verify_inputs():
    prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    bad=[p for p,h in prior.items() if sha(ROOT/p)!=h]
    if bad:raise RuntimeError(f'Prior or preparation inputs changed: {bad}')
    for p,h in json.loads((PREP/'frozen_split_manifest.json').read_text(encoding='utf-8')).items():
        if sha(PREP/p)!=h:raise RuntimeError('Split hash mismatch')
    return len(prior)


def load_labels():
    pt=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv');pt=pt[pt.conservative]
    pt=pt[['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'class_id'})
    hist=pd.read_csv(ROOT/'reports/qa/WP03/historical_category_projection_audit.csv')
    hist=hist[hist.conservative][['id','category']].drop_duplicates().rename(columns={'id':'drug_id','category':'class_id'})
    return {'PT':pt,'historical30':hist}


def positive_lookup(labels):
    if labels.duplicated(['drug_id','class_id']).any():raise ValueError('Duplicate observed record')
    return {c:set(f.drug_id) for c,f in labels.groupby('class_id')}


def proxy_matrix(ids,classes,lookup):
    # 0 means no source record in approved binary PROXY, never verified negative.
    return np.array([[int(d in lookup.get(c,set())) for c in classes] for d in ids],dtype=np.int8).reshape(len(ids),len(classes))


def fit_binary_models(X,train_ids,targets,lookup,C):
    """Only rows already sliced to exact train IDs enter sklearn.fit."""
    if len(X)!=len(train_ids) or len(set(train_ids))!=len(train_ids):raise ValueError('Training identity mismatch')
    fitted={};trace=[]
    for target in targets:
        s=np.array([int(d in lookup.get(target,set())) for d in train_ids])
        p=int(s.sum());u=len(s)-p
        row={'class_id':target,'observed_train_positive':p,'train_unknown_NOT_verified_negative':u,'C':C,'semantics':SEMANTICS}
        if not p or not u:
            row.update(status='NA_single_proxy_outcome',iterations=0,warning='');trace.append(row);continue
        try:
            model=LogisticRegression(C=C,solver='liblinear',l1_ratio=0.0,class_weight=None,tol=1e-8,max_iter=10000,
                                     random_state=SEED,fit_intercept=True,intercept_scaling=1.)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always');model.fit(X,s)
            messages=[str(w.message) for w in caught]
            if any(issubclass(w.category,ConvergenceWarning) for w in caught):
                row.update(status='NA_convergence_warning',iterations=int(model.n_iter_[0]),warning=' | '.join(messages))
            else:
                fitted[target]=(model.coef_[0].copy(),float(model.intercept_[0]))
                row.update(status='fitted',iterations=int(model.n_iter_[0]),warning=' | '.join(messages))
        except Exception as exc:
            row.update(status='NA_fit_error',iterations=0,warning=f'{type(exc).__name__}: {exc}')
        trace.append(row)
    return fitted,trace


def predict_parameters(X,parameters,targets):
    out=np.full((len(X),len(targets)),np.nan)
    for j,target in enumerate(targets):
        if target in parameters:
            coef,intercept=parameters[target];out[:,j]=expit(X@coef+intercept)
    return out


def choose_C(fold_scores):
    """fold_scores: C -> same ordered folds; all-C valid fold intersection."""
    arrays={float(c):np.asarray(a,dtype=float) for c,a in fold_scores.items()}
    valid=np.logical_and.reduce([np.isfinite(a) for a in arrays.values()])
    if not valid.any():return None,{c:np.nan for c in arrays},0
    means={c:float(a[valid].mean()) for c,a in arrays.items()};best=max(means.values())
    chosen=min(c for c,value in means.items() if abs(value-best)<=1e-12)
    return chosen,means,int(valid.sum())


def tune_fold(X,ids,train_ids,val_ids,targets,lookup):
    rows={d:i for i,d in enumerate(ids)};train=sorted(train_ids);val=sorted(val_ids)
    params={};trace={}
    for c in GRID:params[c],trace[c]=fit_binary_models(X[[rows[d] for d in train]],train,targets,lookup,c)
    common=sorted(set.intersection(*(set(p) for p in params.values())))
    scored_ids=val;signature=hashlib.sha256(json.dumps({'validation_ids':val,'classes':common},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    metrics={}
    for c in GRID:
        scores=predict_parameters(X[[rows[d] for d in val]],params[c],common)
        panel=MetricPanel(proxy_matrix(val,common,lookup),scores,val,common)
        metrics[c]={'drug_macro_AP':float(panel.evaluate()['drug_macro_AP'][0]),'valid_drugs':int(np.isfinite(panel.drug_AP).sum()),
                    'validation_input_drugs':len(val),'scoring_classes':len(common),'candidate_fitted_classes':len(params[c]),
                    'scope_hash':signature,'excluded_from_C_comparison':len(targets)-len(common),'semantics':SEMANTICS}
    return params,trace,metrics,common


def save_model_bundle(name,params,trace,metadata):
    targets=sorted(params);width=int(metadata['feature_dimension'])
    coef=np.array([params[c][0] for c in targets]).reshape(len(targets),width)
    intercept=np.array([params[c][1] for c in targets])
    path=MODEL/(name+'.npz')
    np.savez_compressed(path,class_ids=np.array(targets,dtype=str),coef=coef,intercept=intercept,
                        semantics=np.array(SEMANTICS),model_version=np.array(VERSION))
    metadata.update(parameters_file=str(path.relative_to(ROOT)),parameters_sha256=sha(path),fitted_classes=targets,
                    class_fit_trace=trace,semantics=SEMANTICS,model_version=VERSION,sklearn_version=sklearn.__version__)
    write_json(MODEL/(name+'.json'),metadata)


def main():
    QA.mkdir(parents=True,exist_ok=True);MODEL.mkdir(parents=True,exist_ok=True)
    previous=verify_inputs()
    config_path=QA/'run_config.json'
    frozen={**CONFIG,'C_grid':list(GRID),'split_manifest':json.loads((PREP/'frozen_split_manifest.json').read_text(encoding='utf-8'))}
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8'))!=frozen:raise RuntimeError('Run config changed; create new version')
    if (QA/'training_complete.json').exists():raise RuntimeError('Training already completed; do not refit after seeing test results')
    write_json(config_path,frozen)
    write_json(QA/'user_authorization.json',{'status':'APPROVED_BY_USER','scope':'First L2 LR B1/B2 PT and historical30, primary and frozen stress nested CV',
        'preparation_gate_false_is_historical':True,'no_preparation_file_modified':True,'PPI_WP09_authorized':False,'semantics':SEMANTICS})
    prep_files=[p for p in PREP.rglob('*') if p.is_file()]
    write_json(QA/'preparation_input_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(prep_files)})
    parts=pd.read_csv(PREP/'nested_partitions_v1.csv');elig=pd.read_csv(PREP/'prediction_eligibility.csv')
    vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
    schema=json.loads((PREP/'feature_schema_v1.json').read_text(encoding='utf-8'))['features']
    fit_sources=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'))
    secondary=json.loads((PREP/'historical30_reference.json').read_text(encoding='utf-8'))['classes']
    labels=load_labels();lookups={f:positive_lookup(l) for f,l in labels.items()}
    available={m:set(elig[elig.model.eq(m)&elig.eligible].drug_id) for m in ('B1','B2')}
    selection=[];inner_rows=[];class_trace=[];phase=[]
    def metadata(context,family,model,C,train_ids):
        return {'context':context,'family':family,'baseline':model,'C':C,'seed':SEED,'train_drug_ids':sorted(train_ids),
            'transform_fit_sources':fit_sources[context],'target_source':'frozen train vocabulary' if family=='PT' else 'fixed historical30 with semantic warnings',
            'feature_schema':schema[model],'feature_dimension':len(schema[model]),
            'feature_file_sha256':sha(PREP/'features'/(context+'.npz')),'split_manifest':frozen['split_manifest'],
            'prepared_train_graph_bundle_sha256':sha(PREP/'train_only_graphs_v1.pt'),'graph_has_PPI':False}
    start=time.perf_counter()
    with threadpool_limits(limits=1):
        # PHASE A: no outer test prediction or metric in this phase.
        for protocol in ('primary','stress'):
            for ofold in range(1,6):
                for family in ('PT','historical30'):
                    for model in ('B1','B2'):
                        fold_values={c:[] for c in GRID}
                        for ifold in range(1,4):
                            context=f'{protocol}_o{ofold:02}_i{ifold:02}';sub=parts[parts.context.eq(context)]
                            train=set(sub[sub.split.eq('train')].drug_id)&available[model]
                            val=set(sub[sub.split.eq('validation')].drug_id)&available[model]
                            targets=vocab[context][model] if family=='PT' else secondary
                            with np.load(PREP/'features'/(context+'.npz'),allow_pickle=False) as arr:
                                params,traces,metrics,common=tune_fold(arr[model],arr['drug_ids'],train,val,targets,lookups[family])
                            for c in GRID:
                                name=f'{context}_{family}_{model}_C{c:g}'
                                md=metadata(context,family,model,c,train);md.update(phase='inner_train_fit',validation_drug_ids=sorted(val),comparison_targets=common)
                                save_model_bundle(name,params[c],traces[c],md)
                                fold_values[c].append(metrics[c]['drug_macro_AP'])
                                inner_rows.append({'protocol':protocol,'outer_fold':ofold,'inner_fold':ifold,'context':context,
                                    'family':family,'model':model,'C':c,**metrics[c]})
                                class_trace.extend({'context':context,'phase':'inner','family':family,'model':model,**r} for r in traces[c])
                        chosen,means,valid=choose_C(fold_values)
                        selection.append({'protocol':protocol,'outer_fold':ofold,'family':family,'model':model,'selected_C':chosen,
                            'valid_inner_folds':valid,'C0.1_mean_drug_AP':means[.1],'C1_mean_drug_AP':means[1.],'C10_mean_drug_AP':means[10.],
                            'status':'selected_inner_only' if chosen is not None else 'NA_no_common_valid_inner_fold','semantics':SEMANTICS})
                print(f'Inner selection complete: {protocol} outer {ofold}/5; no outer test scoring',flush=True)
        write_csv(QA/'inner_selection_metrics.csv',pd.DataFrame(inner_rows));write_csv(QA/'selected_C.csv',pd.DataFrame(selection))
        write_json(QA/'selection_complete_before_outer_scoring.json',{'selected_C_sha256':sha(QA/'selected_C.csv'),
            'inner_metrics_sha256':sha(QA/'inner_selection_metrics.csv'),'outer_test_scoring_performed':False,'elapsed_seconds':time.perf_counter()-start})
        # PHASE B: final fits only outer train; then unlabeled query features scored.
        predictions=[];output_rows=[];outer_bundles=[]
        for choice in selection:
            protocol=choice['protocol'];ofold=choice['outer_fold'];family=choice['family'];model=choice['model'];c=choice['selected_C']
            context=f'{protocol}_o{ofold:02}_final';sub=parts[parts.context.eq(context)]
            train=set(sub[sub.split.eq('train')].drug_id)&available[model];test=sorted(sub[sub.split.eq('test')].drug_id)
            targets=vocab[context][model] if family=='PT' else secondary
            with np.load(PREP/'features'/(context+'.npz'),allow_pickle=False) as arr:
                ids=list(arr['drug_ids']);rows={d:i for i,d in enumerate(ids)};X=arr[model]
                if c is None:params={};trace=[{'class_id':t,'C':None,'status':'NA_no_selected_C','semantics':SEMANTICS} for t in targets]
                else:params,trace=fit_binary_models(X[[rows[d] for d in sorted(train)]],sorted(train),targets,lookups[family],c)
                usable=[d for d in test if d in available[model]]
                scores=predict_parameters(X[[rows[d] for d in usable]],params,targets)
            name=f'{context}_{family}_{model}_selected'
            md=metadata(context,family,model,c,train);md.update(phase='outer_train_final_fit',test_drug_ids_never_fit=test,
                declared_target_dictionary=targets,selected_C_trace=choice,selection_file_sha256=sha(QA/'selected_C.csv'))
            save_model_bundle(name,params,trace,md)
            class_trace.extend({'context':context,'phase':'outer','family':family,'model':model,**r} for r in trace)
            outer_bundles.append({'context':context,'protocol':protocol,'outer_fold':ofold,'family':family,'model':model,
                'selected_C':c,'train_input_drugs':len(train),'declared_targets':len(targets),'fitted_targets':len(params),
                'test_cohort_drugs':len(test),'test_input_eligible':len(usable),'parameters_file':str((MODEL/(name+'.npz')).relative_to(ROOT)),
                'semantics':SEMANTICS})
            for i,drug in enumerate(usable):
                for j,target in enumerate(targets):
                    if not np.isfinite(scores[i,j]):continue
                    predictions.append({'protocol':protocol,'outer_fold':ofold,'family':family,'model':model,'drug_id':drug,
                        'class_id':target,'observed_record_s':int(drug in lookups[family].get(target,set())),
                        'score_observed_record_proxy':scores[i,j],'selected_C':c,'model_version':VERSION,'semantics':SEMANTICS})
            for drug in test:
                status='ABSTAIN_no_input' if drug not in available[model] else 'NO_SCORE_fit_unavailable' if not params else 'OOF_prediction_available'
                output_rows.append({'protocol':protocol,'outer_fold':ofold,'family':family,'model':model,'drug_id':drug,'status':status,
                    'declared_targets':len(targets),'scored_targets':len(params) if drug in available[model] else 0,'semantics':SEMANTICS})
            print(f'Outer fit/query complete: {protocol} {ofold} {family} {model}, C={c}',flush=True)
    write_csv(QA/'oof_predictions.csv',pd.DataFrame(predictions));write_csv(QA/'prediction_status_all62.csv',pd.DataFrame(output_rows))
    write_csv(QA/'class_fit_trace.csv',pd.DataFrame(class_trace));write_csv(QA/'outer_model_coverage.csv',pd.DataFrame(outer_bundles))
    write_json(QA/'training_complete.json',{'model_version':VERSION,'classifier_fits_attempted':len(class_trace),
        'outer_bundles':len(outer_bundles),'OOF_scored_pairs':len(predictions),'prior_files_verified':previous,
        'elapsed_seconds':time.perf_counter()-start,'selected_C_sha256':sha(QA/'selected_C.csv'),
        'semantics':SEMANTICS,'WP09_started':False})
    verify_inputs();print('Training/query stages complete; frozen inputs unchanged. No evaluation-driven refitting.',flush=True)


if __name__=='__main__':main()
