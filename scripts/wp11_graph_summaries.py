"""Gerçek açıklama dosyalarını akışla denetler; görsel veri tabloları çıkarır."""
import json
import numpy as np
import pandas as pd
from wp11_graph_policy import ROOT,QA,ROLES,verify,preserve
from wp11_linear_shap import write_json
import wp10_train as old


def run():
    if (QA/'summary_complete.json').exists():raise RuntimeError('Summary v1 already exists')
    complete=json.loads((QA/'analysis_complete.json').read_text());s=pd.read_csv(QA/'intervention_summary.csv')
    totals=[];streamchecks=[];native=json.loads((QA/'frozen_contexts.json').read_text());vocab={c['context']:set(c['fitted_targets']) for c in native}
    for kind in ['role','ppi']:
        n=0;err=0.;nonfinite=0;exact0=0;near0=0;counts={}
        for block in pd.read_csv(QA/(kind+'_contributions.csv.gz'),chunksize=50000):
            n+=len(block);e=np.abs(block.original_logit-block.intervened_logit-block.delta_z);err=max(err,float(e.max()));nonfinite+=int(block.delta_z.isna().sum());exact0+=int(block.delta_z.eq(0).sum());near0+=int(block.delta_z.abs().le(1e-7).sum())
            for ctx,b in block.groupby('context'):
                assert set(b.class_id)<=vocab[ctx]
                for mode,part in b.groupby('mode'):counts[(ctx,mode)]=counts.get((ctx,mode),0)+len(part)
            assert block.status.isin(['OK','NA_after_deletion_no_input']).all()
        assert n==complete['contribution_rows'][kind] and err<=1e-5
        for ctx,classes in vocab.items():
            for mode in ['fixed','delete']:
                jobs=len(s[s.kind.eq(kind)&s.context.eq(ctx)&s['mode'].eq(mode)]);assert counts[(ctx,mode)]==jobs*len(classes)
        streamchecks.append({'kind':kind,'rows':n,'max_delta_identity_roundtrip_error':err,'NA_rows':nonfinite,'exact_zero_delta_rows':exact0,'abs_delta_at_most_1e7_rows':near0,'native_PT_scope_only':True})
    for (p,kind,mode),d in s.groupby(['protocol','kind','mode']):
        totals.append({'protocol':p,'kind':kind,'mode':mode,'interventions':len(d),'finite_interventions':int(d.PT_count.gt(0).sum()),'NA_interventions':int(d.PT_count.eq(0).sum()),'native_PT_pair_count':int(d.PT_count.sum()),'mean_of_native_PT_mean_abs_delta':d.mean_abs_delta.mean(),'median_of_native_PT_mean_abs_delta':d.mean_abs_delta.median(),'max_abs_delta_any_PT':d.max_abs_delta.max(),'near_zero_PT_pairs_abs_tol_1e7':int(d.zero_n_abs_tol_1e7.sum())})
    pd.DataFrame(totals).to_csv(QA/'descriptive_summary.csv',index=False,encoding='utf-8-sig');pd.DataFrame(streamchecks).to_csv(QA/'compressed_table_stream_checks.csv',index=False,encoding='utf-8-sig')
    # Pair identical query/edge keys,never fill missing target dictionaries.
    keys=['kind','context','protocol','drug_id','role','protein_id','protein_a','protein_b']
    for key in ['role','protein_id','protein_a','protein_b']:s[key]=s[key].fillna('')
    fixed=s[s['mode'].eq('fixed')].drop(columns='mode');deleted=s[s['mode'].eq('delete')].drop(columns='mode')
    paired=fixed.merge(deleted,on=keys,validate='one_to_one',suffixes=('_fixed','_delete'))
    paired['mean_abs_delta_delete_minus_fixed']=paired.mean_abs_delta_delete-paired.mean_abs_delta_fixed
    paired.to_csv(QA/'mask_vs_deletion_sensitivity.csv',index=False,encoding='utf-8-sig')
    ex=pd.read_csv(QA/'examples_frozen.csv');networks=[];case1=ex[ex.context.eq('primary_o01_final')].iloc[0];case2=ex[ex.protocol.eq('primary')&ex.drug_id.eq('DB00199')].iloc[0]
    contributions=pd.read_csv(QA/'example_contributions.csv');names=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','name']).drop_duplicates().set_index('id')['name'].to_dict()
    for case in [case1,case2]:
        g=old.load_bundle(case.context,'train');q=old.load_bundle(case.context,'query');di=list(q['drug_ids']).index(case.drug_id);pool=list(g['protein_ids'])+list(q['unseen_protein_ids']);nodes={};edges=[]
        selected=contributions[contributions.context.eq(case.context)&contributions.drug_id.eq(case.drug_id)&contributions.class_id.eq(case.class_id)&contributions['mode'].eq('fixed')]
        for role in ROLES:
            for pi in q['role_'+role][1,q['role_'+role][0]==di]:
                acc=pool[pi];nodes[acc]={'id':acc,'query_role_protein':True,'train_pool':bool(pi<len(g['protein_ids']))}
                v=selected[selected.kind.eq('role')&selected.role.eq(role)&selected.protein_id.eq(acc)];assert len(v)==1
                edges.append({'kind':'role','source':case.drug_id,'target':acc,'role':role,'delta_z':float(v.delta_z.iloc[0])})
        used={pool.index(p) for p in nodes}
        for a,b in g['ppi_pairs_700'].T:
            if a not in used and b not in used:continue
            aa,bb=g['protein_ids'][[a,b]]
            for acc in [aa,bb]:nodes.setdefault(acc,{'id':acc,'query_role_protein':False,'train_pool':True})
            v=selected[selected.kind.eq('ppi')&selected.protein_a.eq(aa)&selected.protein_b.eq(bb)];assert len(v)==1
            edges.append({'kind':'ppi','source':aa,'target':bb,'role':'PPI','delta_z':float(v.delta_z.iloc[0])})
        networks.append({'context':case.context,'drug_id':case.drug_id,'drug_name':names[case.drug_id],'class_id':case.class_id,'selection':'frozen primary outer1 first example / predeclared Erythromycin','layout_seed':20261106,'nodes':list(nodes.values()),'edges':edges})
    write_json(QA/'real_networks.json',networks)
    verify('policy_commit_before_attribution.json');verify('input_manifest.json');preserve()
    write_json(QA/'summary_complete.json',{'status':'PASS','stream_checked_rows':sum(d['rows'] for d in streamchecks),'descriptive_tables_only':True,'no_new_model_run':True,'WP11_final_closed':False,'WP12':False})
    print(pd.DataFrame(totals).to_string(index=False));print(streamchecks)


if __name__=='__main__':run()
