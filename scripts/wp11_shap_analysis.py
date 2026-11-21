"""Dondurulmuş B1 SHAP sözleşmesinin etiketsiz, yeniden fitsiz uygulaması."""
import json,platform,sys
import numpy as np
import pandas as pd
from wp11_linear_shap import ROOT,QA,PREP,FEATURES,CHEM,sha,write_json,csv,preserve,load_context,linear_shap,enumerate_shap


def verify_manifest(name):
    manifest=json.loads((QA/name).read_text(encoding='utf-8'))
    bad=[p for p,h in manifest.items() if sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(manifest)


def run():
    if (QA/'analysis_summary.json').exists():raise RuntimeError('Versioned outputs already exist;do not overwrite')
    preserved=preserve();verify_manifest('policy_commit_before_explanations.json');verify_manifest('input_manifest.json')
    policy=json.loads((QA/'policy_v1.json').read_text());common=json.loads((QA/'common_PT_intersections.json').read_text())
    examples=pd.read_csv(QA/'examples_frozen_before_explanations.csv')
    old=pd.read_csv(ROOT/'reports/qa/WP08/baseline_v1/oof_predictions.csv',usecols=['protocol','outer_fold','family','model','drug_id','class_id','score_observed_record_proxy'])
    old=old[old.model.eq('B1')&old.family.eq('PT')]
    if old.duplicated(['protocol','outer_fold','drug_id','class_id']).any():raise AssertionError('Duplicate OOF keys')
    raw=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv').set_index('id')
    stats=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text())
    names=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['meddra_cui','term']).drop_duplicates().sort_values(['meddra_cui','term']).groupby('meddra_cui').term.agg(' | '.join).to_dict()
    locals_=[];pairs=[];globals_=[];coverage=[];targets=[];enums=[];stability=[];checks=[];background=[]
    for context in policy['contexts']:
        c=load_context(context);md=c['metadata'];protocol=context.split('_')[0];fold=int(context.split('_')[1][1:]);x=c['test_x'];b=c['train_x'];w=c['coef'];a=c['intercept'];classes=c['classes']
        out=linear_shap(x,b,w,a);phi=out['phi'];n,k,_=phi.shape
        add=float(np.max(np.abs(out['base'][None,:]+phi.sum(2)-out['logit'])))
        keys=pd.DataFrame({'drug_id':np.repeat(c['test_ids'],k),'class_id':np.tile(classes,n),'logit':out['logit'].ravel(),'base':np.tile(out['base'],n),'proxy_score':out['proxy_score'].ravel(),'sum_phi':phi.sum(2).ravel()})
        saved=old[old.protocol.eq(protocol)&old.outer_fold.eq(fold)].drop(columns=['protocol','outer_fold','family','model'])
        keys=keys.merge(saved,on=['drug_id','class_id'],how='outer',validate='one_to_one',indicator=True)
        if not keys['_merge'].eq('both').all():raise AssertionError('Saved OOF coverage mismatch')
        keys=keys.drop(columns='_merge');keys['additivity_error']=keys.base+keys.sum_phi-keys.logit;keys['OOF_score_error']=keys.proxy_score-keys.score_observed_record_proxy
        error=float(keys.OOF_score_error.abs().max())
        keys.insert(0,'context',context);keys.insert(1,'protocol',protocol);keys.insert(2,'outer_fold',fold);pairs.append(keys)
        rawx=raw.loc[c['test_ids'],CHEM].to_numpy(float);rawb=raw.loc[c['train_ids'],CHEM].to_numpy(float)
        chemstats=stats[context]['chemistry'];scale=np.array([chemstats['scale'][f] for f in CHEM]);mean=np.array([chemstats['mean'][f] for f in CHEM])
        assert np.allclose((rawx-mean)/scale,x[:,:5],rtol=0,atol=1e-12)
        rawphi=(rawx[:,None,:]-rawb.mean(0)[None,None,:])*(w[:,:5]/scale)[None,:,:]
        rawerr=float(np.max(np.abs(rawphi-phi[:,:,:5])))
        frame=pd.DataFrame({'context':context,'protocol':protocol,'outer_fold':fold,'drug_id':np.repeat(c['test_ids'],k*6),'class_id':np.tile(np.repeat(classes,6),n),'feature':np.tile(FEATURES,n*k),'feature_type':np.tile(['chemistry']*5+['availability_mask'],n*k),'standardized_value':np.repeat(x[:,None,:],k,axis=1).ravel(),'raw_value':np.repeat(np.column_stack([rawx,x[:,5]])[:,None,:],k,axis=1).ravel(),'background_mean_standardized':np.tile(out['background_mean'],n*k),'coefficient':np.tile(w.ravel(),n),'SHAP_logit':phi.ravel()})
        locals_.append(frame)
        g=frame.groupby(['context','protocol','outer_fold','class_id','feature','feature_type'],sort=False).SHAP_logit.agg(mean_signed='mean',mean_abs=lambda v:np.abs(v).mean(),n_test_drugs='size').reset_index();globals_.append(g)
        coverage.append({'context':context,'protocol':protocol,'outer_fold':fold,'background_train':len(b),'test_inventory':len(c['inventory_test_ids']),'test_explained':n,'test_abstain':len(c['inventory_test_ids'])-n,'declared_PT':len(md['declared_target_dictionary']),'fitted_PT':k,'NA_PT':len(set(md['declared_target_dictionary'])-set(classes)),'explained_pairs':n*k,'protocol_common_PT':len(common[protocol])})
        for cui in md['declared_target_dictionary']:
            trace=next((t for t in md['class_fit_trace'] if t['class_id']==cui),{})
            targets.append({'context':context,'class_id':cui,'term':names.get(cui,''),'status':'explained' if cui in classes else 'NA_not_fitted','saved_fit_status':trace.get('status','NA'),'test_drugs_explained':n if cui in classes else 0})
        for i,f in enumerate(FEATURES):background.append({'context':context,'feature':f,'n_train':len(b),'mean_standardized':b[:,i].mean(),'std_standardized_ddof0':b[:,i].std(),'min':b[:,i].min(),'max':b[:,i].max()})
        for row in examples[examples.context.eq(context)].itertuples():
            di=c['test_ids'].index(row.drug_id);ki=classes.index(row.class_id);enum,base=enumerate_shap(x[di],b,w[ki],a[ki])
            enums.append({'context':context,'drug_id':row.drug_id,'class_id':row.class_id,'coalitions':64,'max_abs_SHAP_error':np.max(np.abs(enum-phi[di,ki])),'base_error':abs(base-out['base'][ki])})
        # Leave-one-background-row-out changes attribution/reference, NEVER frozen predictions.
        loo_mu=(b.sum(0)[None,:]-b)/(len(b)-1);delta=w[None,:,:]*(out['background_mean'][None,None,:]-loo_mu[:,None,:])
        flipped=np.zeros((k,6),int);valid=np.zeros((k,6),int);maxconservation=0.
        for j,m in enumerate(loo_mu):
            alt=phi+delta[j][None,:,:];base=a+w@m
            maxconservation=max(maxconservation,float(np.max(np.abs(base[None,:]+alt.sum(2)-out['logit']))))
            eligible=(np.abs(phi)>1e-12)&(np.abs(alt)>1e-12)
            valid+=eligible.sum(0);flipped+=((np.sign(phi)!=np.sign(alt))&eligible).sum(0)
        for ki,cui in enumerate(classes):
            for fi,f in enumerate(FEATURES):stability.append({'context':context,'protocol':protocol,'class_id':cui,'feature':f,'n_LOO_backgrounds':len(b),'max_abs_delta_SHAP':np.abs(delta[:,ki,fi]).max(),'mean_abs_delta_SHAP':np.abs(delta[:,ki,fi]).mean(),'nonzero_sign_flip_n':int(flipped[ki,fi]),'nonzero_sign_comparisons':int(valid[ki,fi]),'nonzero_sign_flip_fraction':float(flipped[ki,fi]/valid[ki,fi]) if valid[ki,fi] else np.nan})
        order=linear_shap(x[::-1],b[::-1],w[::-1],a[::-1]);ordererr=float(np.max(np.abs(order['phi'][::-1,::-1]-phi)))
        repeat=float(np.max(np.abs(linear_shap(x,b,w,a)['phi']-phi)))
        checks.append({'context':context,'max_additivity_error':add,'max_OOF_score_error':error,'max_raw_unit_SHAP_error':rawerr,'max_order_error':ordererr,'max_repeat_error':repeat,'max_LOO_conservation_error':maxconservation,'max_mask_abs_SHAP':float(np.abs(phi[:,:,5]).max())})
        if max(add,rawerr,maxconservation)>1e-10 or max(error,ordererr,repeat)>1e-12:raise AssertionError(checks[-1])
    local=pd.concat(locals_,ignore_index=True);pair=pd.concat(pairs,ignore_index=True);native=pd.concat(globals_,ignore_index=True)
    csv('local_shap.csv',local);csv('local_pair_outputs.csv',pair);csv('global_native_context_PT.csv',native)
    csv('coverage_summary.csv',pd.DataFrame(coverage));csv('target_coverage.csv',pd.DataFrame(targets));csv('background_summary.csv',pd.DataFrame(background));csv('enumeration_checks.csv',pd.DataFrame(enums));csv('stability_LOO.csv',pd.DataFrame(stability));csv('consistency_checks.csv',pd.DataFrame(checks))
    example=local.merge(examples[['context','drug_id','class_id','selection']],on=['context','drug_id','class_id'],validate='many_to_one');example['term']=example.class_id.map(names);csv('example_local_shap.csv',example)
    commonrows=pd.concat([local[local.protocol.eq(p)&local.class_id.isin(cuis)] for p,cuis in common.items()],ignore_index=True)
    commonPT=commonrows.groupby(['protocol','class_id','feature','feature_type']).SHAP_logit.agg(mean_signed='mean',mean_abs=lambda v:np.abs(v).mean(),n_drugs='size').reset_index()
    overall=commonrows.groupby(['protocol','feature','feature_type']).SHAP_logit.agg(mean_signed='mean',mean_abs=lambda v:np.abs(v).mean(),n_drug_PT='size').reset_index()
    csv('global_common_PT.csv',commonPT);csv('global_common_summary.csv',overall)
    summary={'version':policy['version'],'models':len(coverage),'local_pairs':len(pair),'local_feature_rows':len(local),'examples':len(enums),'coalition_evaluations':64*len(enums),'common_PT_counts':{p:len(v) for p,v in common.items()},'max_errors':pd.DataFrame(checks).drop(columns='context').max().to_dict(),'enumeration_max_error':pd.DataFrame(enums).max_abs_SHAP_error.max(),'per_protocol_test_explained':pair.groupby('protocol').drug_id.nunique().to_dict(),'preserved_prior_files':preserved,'model_fit':False,'graph_attribution':False,'test_outcomes_read':False,'WP12':False,'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'platform':platform.platform(),'semantics':policy['semantics']}
    verify_manifest('policy_commit_before_explanations.json');verify_manifest('input_manifest.json');preserve()
    write_json(QA/'analysis_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':run()
