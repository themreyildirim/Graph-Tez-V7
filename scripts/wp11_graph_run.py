"""Kayıtlı A1P1 modelinde tekil graph perturbation; fit/etiket kanalı yok."""
import copy,gzip,json,time,traceback,contextlib
from unittest.mock import patch
import numpy as np
import pandas as pd
from wp11_graph_policy import ROOT,QA,ROLES,preserve,verify
from wp11_linear_shap import sha,write_json
from wp11_graph_forward import (torch,numeric_digest,ExplanationCache,cache_for,query_logits,resolve_relation,pair_index_by_ids)
import wp10_train as old
from wp10_molecular_encoder import initialized_model
from wp09_data import validate_bundle


def load(context,store=None):
    md=json.loads((ROOT/f'models/WP10_factorial_training_v1/{context}_A1P1.json').read_text())
    assert md['variant']=='A1P1' and sha(ROOT/md['parameters_file'])==md['parameters_sha256']
    model=initialized_model(md['seed'],len(md['fitted_targets']))
    with np.load(ROOT/md['parameters_file'],allow_pickle=False) as a:model.load_state_dict({k:torch.from_numpy(a[k].copy()) for k in a.files})
    model.eval();model.requires_grad_(False)
    assert numeric_digest(model.state_dict())==md['selected_state_sha256']
    g=old.load_bundle(context,'train');q=old.load_bundle(context,'query');validate_bundle(g,q)
    assert np.all(q['split']=='test') and not set(g['drug_ids'])&set(q['drug_ids'])
    store=old.get_store() if store is None else store
    with torch.no_grad():
        train=model.encode_train(g,store.make_batch(g['drug_ids']),'A1P1')
        ref=model.encode_query(g,q,store.make_batch(q['drug_ids']),train['cache'])
        unseen=model.base.protein(torch.as_tensor(q['unseen_protein_x'],dtype=torch.float32),torch.empty((2,0),dtype=torch.long))
    cache=ExplanationCache(train['cache'].protein_h.clone(),numeric_digest(g),numeric_digest(model.state_dict()),'none')
    return {'model':model,'md':md,'g':g,'q':q,'cache':cache,'unseen':unseen,'atom_block':ref['molecular_block'].clone(),'atom_mask':ref['effective_atom_mask'].clone(),'reference':ref['logits'].clone()}


def forward(s,cache=None,relation=None,mode='fixed'):
    return query_logits(s['model'],s['q'],s['cache'] if cache is None else cache,s['unseen'],s['atom_block'],s['atom_mask'],numeric_digest(s['g']),relation,mode)


def permute_protein_indices(g,q):
    g=copy.deepcopy(g);q=copy.deepcopy(q);n=len(g['protein_ids']);perm=np.arange(n)[::-1];inverse=np.argsort(perm)
    g['protein_ids']=g['protein_ids'][perm].copy();g['protein_x']=g['protein_x'][perm].copy()
    for threshold in [400,700,900]:g[f'ppi_pairs_{threshold}']=np.array(sorted(tuple(sorted(inverse[p])) for p in g[f'ppi_pairs_{threshold}'].T),dtype=np.int64).reshape(-1,2).T
    for r in ROLES:
        g['role_'+r][1]=inverse[g['role_'+r][1]]
        arr=q['role_'+r][1];seen=arr<n;arr[seen]=inverse[arr[seen]]
    return g,q


def stability_probe(s,store):
    """Önceden belirlenen ilk gerçek ilişki/ilk PPI çifti; sonuç temelli seçilmez."""
    model,g,q=s['model'],s['g'],s['q'];records=[]
    pick=next(((r,int(d),int(p)) for r in ROLES for d,p in q['role_'+r].T),None)
    # Reverse query order, remap role indices and molecular blocks by identity.
    order=list(q['drug_ids'][::-1]);qr=old.select_query(q,order,len(g['protein_ids']))
    ix=[list(q['drug_ids']).index(d) for d in qr['drug_ids']]
    sr={**s,'q':qr,'atom_block':s['atom_block'][ix],'atom_mask':s['atom_mask'][ix]}
    # old.select_query may remap/drop unseen proteins;rebuild their self-only rows.
    sr['unseen']=model.base.protein(torch.as_tensor(qr['unseen_protein_x'],dtype=torch.float32),torch.empty((2,0),dtype=torch.long))
    if pick:
        r,d,p=pick;drug=q['drug_ids'][d];pool=list(g['protein_ids'])+list(q['unseen_protein_ids']);accession=pool[p]
        new=resolve_relation(g,qr,drug,r,accession)
        a=forward(s,relation=pick)['logits'];b=forward(sr,relation=new)['logits']
        error=float(torch.nan_to_num(a-torch.stack([b[list(qr['drug_ids']).index(i)] for i in q['drug_ids']])).abs().max())
        records.append({'context':s['md']['context'],'check':'query_order_role_mask','max_abs_logit_error':error})
        single=old.select_query(q,[drug],len(g['protein_ids']));single_s={**s,'q':single,'atom_block':s['atom_block'][d:d+1],'atom_mask':s['atom_mask'][d:d+1]}
        single_s['unseen']=model.base.protein(torch.as_tensor(single['unseen_protein_x'],dtype=torch.float32),torch.empty((2,0),dtype=torch.long))
        rel=resolve_relation(g,single,drug,r,accession);one=forward(single_s,relation=rel)['logits'][0]
        records.append({'context':s['md']['context'],'check':'query_alone_role_mask','max_abs_logit_error':float(torch.nan_to_num(one-a[d]).abs().max())})
    gp,qp=permute_protein_indices(g,q);cp=cache_for(model,gp)
    sp={**s,'g':gp,'q':qp,'cache':cp};base=forward(sp)['logits']
    records.append({'context':s['md']['context'],'check':'protein_index_permutation_no_mask','max_abs_logit_error':float(torch.nan_to_num(base-s['reference']).abs().max())})
    if g['ppi_pairs_700'].shape[1]:
        ids=g['protein_ids'][g['ppi_pairs_700'][:,0]];index=pair_index_by_ids(gp,*ids[::-1]);c=cache_for(model,g,0);alt=cache_for(model,gp,index)
        a=forward(s,cache=c)['logits'];b=forward(sp,cache=alt)['logits']
        records.append({'context':s['md']['context'],'check':'protein_permutation_PPI_mask_reverse_endpoint_ID','max_abs_logit_error':float(torch.nan_to_num(a-b).abs().max())})
    assert all(r['max_abs_logit_error']<=1e-5 for r in records)
    return records


def run():
    if (QA/'analysis_complete.json').exists():raise RuntimeError('Graph v1 already exists')
    for f in ['role_contributions.csv.gz','ppi_contributions.csv.gz']:
        if (QA/f).exists():raise RuntimeError('Partial output exists;retain failure evidence,do not overwrite')
    gate=json.loads((QA/'synthetic_gate_PASS.json').read_text());assert gate['status']=='PASS' and gate['tests']==10
    assert sha(QA/'synthetic_tests_before_real.txt')==gate['log_sha256']
    verify('policy_commit_before_attribution.json');verify('input_manifest.json');preserve()
    write_json(QA/'real_attribution_started.json',{'time_ns':time.time_ns(),'synthetic_gate_sha256':sha(QA/'synthetic_gate_PASS.json'),'policy_commit_sha256':sha(QA/'policy_commit_before_attribution.json')})
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    contexts=json.loads((QA/'frozen_contexts.json').read_text());examples=pd.read_csv(QA/'examples_frozen.csv')
    oof=pd.read_csv(ROOT/'reports/qa/WP10/training_v1/oof_predictions.csv',usecols=['protocol','outer_fold','model','drug_id','class_id','score_observed_record_proxy']);oof=oof[oof.model.eq('A1P1')]
    mapping=pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv');strict=mapping[mapping.strict_taxon_match&mapping.network_taxid.eq(9606)]
    sid=dict(zip(strict.accession,strict.string_id));source=pd.read_csv(ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv');source=source[source.network_taxid.eq(9606)&source.mapping_scope.eq('exact_taxon')&~source.score_conflict&source.combined_score.ge(700)]
    allowed={tuple(sorted([a,b])) for a,b in zip(source.protein1,source.protein2)}
    rows=[];scopes=[];paths=[];absences=[];allsummary=[];example_rows=[];consistency=[];stability=[];edge_scope=[];target_scope=[];native_global=[];counts={'role':0,'ppi':0}
    headers={'role':False,'ppi':False};guard_calls=[]
    def forbidden(*args,**kwargs):guard_calls.append('forbidden_training');raise AssertionError('Training/optimizer/backward forbidden in WP11')
    with contextlib.ExitStack() as guards:
        for obj,name in [(old,'fit_model'),(old,'training'),(old,'run_job'),(torch.optim.Optimizer,'__init__'),(torch.Tensor,'backward')]:guards.enter_context(patch.object(obj,name,forbidden))
        streams={k:guards.enter_context(gzip.open(QA/(k+'_contributions.csv.gz'),'xt',encoding='utf-8')) for k in ['role','ppi']}
        store=old.get_store()
        with torch.no_grad():
            for frozen in contexts:
                context=frozen['context'];s=load(context,store);md=s['md'];g=s['g'];q=s['q'];model=s['model'];protocol=md['protocol'];fold=md['outer_fold'];targets=md['fitted_targets'];k=len(targets);pool=list(g['protein_ids'])+list(q['unseen_protein_ids'])
                before={name:numeric_digest(value if isinstance(value,dict) else {'tensor':value}) for name,value in [('g',g),('q',q),('model',model.state_dict()),('cache',s['cache'].protein_h)]}
                assert q['drug_ids'].tolist()==frozen['test_ids'] and targets==frozen['fitted_targets'] and list(g['drug_ids'])==frozen['train_drug_ids']
                base=forward(s)['logits'];ref=s['reference'];referr=float(torch.nan_to_num(base-ref).abs().max());assert referr<=1e-5
                cp=cache_for(model,g);cacheerr=float((cp.protein_h-s['cache'].protein_h).abs().max());assert cacheerr<=1e-5
                saved=oof[oof.protocol.eq(protocol)&oof.outer_fold.eq(fold)];errors=[]
                for di,d in enumerate(q['drug_ids']):
                    if not q['eligible'][di]:continue
                    expected=saved[saved.drug_id.eq(d)].set_index('class_id').loc[targets].score_observed_record_proxy.to_numpy()
                    errors.extend(np.abs(torch.sigmoid(base[di]).numpy()-expected))
                    for j,cui in enumerate(targets):rows.append({'context':context,'protocol':protocol,'drug_id':d,'class_id':cui,'original_logit':float(base[di,j]),'OOF_proxy_score':float(torch.sigmoid(base[di,j]))})
                assert len(errors)==len(saved) and max(errors)<=1e-7
                for cui in md['declared_train_targets']:target_scope.append({'context':context,'class_id':cui,'status':'fitted_explained' if cui in targets else 'NA_not_fitted'})
                frame=[];rolejobs=0;ppijobs=0;repeaterr=0.;isolationerr=0.;finite_delete_NA=0
                def record(kind,di,fields,mode,changed):
                    nonlocal repeaterr,finite_delete_NA
                    original=base[di].numpy();altered=changed['logits'][di].numpy();delta=original-altered
                    status='OK' if np.isfinite(altered).all() else 'NA_after_deletion_no_input'
                    if status!='OK':finite_delete_NA+=1
                    block=pd.DataFrame({'context':context,'protocol':protocol,'outer_fold':fold,'drug_id':q['drug_ids'][di],'class_id':targets,'mode':mode,**fields,'original_logit':original,'intervened_logit':altered,'delta_z':delta,'status':status})
                    counts[kind]+=len(block);block.to_csv(streams[kind],index=False,header=not headers[kind],lineterminator='\n');headers[kind]=True
                    v=delta[np.isfinite(delta)];allsummary.append({'kind':kind,'context':context,'protocol':protocol,'drug_id':q['drug_ids'][di],'mode':mode,**fields,'status':status,'PT_count':len(v),'mean_signed_delta':float(v.mean()) if len(v) else np.nan,'mean_abs_delta':float(np.abs(v).mean()) if len(v) else np.nan,'max_abs_delta':float(np.abs(v).max()) if len(v) else np.nan,'zero_n_abs_tol_1e7':int((np.abs(v)<=1e-7).sum())})
                    selected=examples[examples.context.eq(context)&examples.drug_id.eq(q['drug_ids'][di])].class_id
                    if len(selected):example_rows.extend(block[block.class_id.isin(selected)].assign(kind=kind).to_dict('records'))
                    frame.append(block.assign(kind=kind))
                for di,d in enumerate(q['drug_ids']):
                    used=set();link_count=0
                    for role in ROLES:
                        ids=q['role_'+role][1,q['role_'+role][0]==di];link_count+=len(ids);used.update(ids.tolist())
                        if not len(ids):absences.append({'context':context,'protocol':protocol,'drug_id':d,'kind':'role','role':role,'status':'NA_abstain_no_input' if not q['eligible'][di] else 'NA_no_typed_role_relation'})
                        for pi in ids:
                            seen=pi<len(g['protein_ids']);degree=int((g['ppi_pairs_700']==pi).sum()) if seen else 0
                            paths.append({'context':context,'protocol':protocol,'drug_id':d,'role':role,'protein_id':pool[pi],'train_pool':seen,'STRING700_degree':degree,'PPI_path_status':'present' if degree else 'NA_unseen_self_only' if not seen else 'NA_no_incident_train_PPI'})
                            rel=resolve_relation(g,q,d,role,pool[pi]);assert rel==(role,di,int(pi))
                            for mode in ['fixed','delete']:
                                changed=forward(s,relation=rel,mode=mode);again=forward(s,relation=rel,mode=mode)
                                repeaterr=max(repeaterr,float(torch.nan_to_num(changed['logits']-again['logits']).abs().max()))
                                other=[i for i in range(len(q['drug_ids'])) if i!=di];isolationerr=max(isolationerr,float(torch.nan_to_num(changed['logits'][other]-base[other]).abs().max()))
                                record('role',di,{'role':role,'protein_id':pool[pi],'protein_a':'','protein_b':''},mode,changed)
                            rolejobs+=1
                    touches=sum(a in used or b in used for a,b in g['ppi_pairs_700'].T)
                    if not touches:absences.append({'context':context,'protocol':protocol,'drug_id':d,'kind':'PPI','role':'','status':'NA_abstain_no_input' if not q['eligible'][di] else 'NA_no_PPI_to_query_role_path'})
                    scopes.append({'context':context,'protocol':protocol,'drug_id':d,'eligible':bool(q['eligible'][di]),'role_relations':link_count,'applicable_PPI_pairs':touches,'PPI_status':'present' if touches else 'NA_no_path'})
                for ei,(a,b) in enumerate(g['ppi_pairs_700'].T):
                    aa,bb=g['protein_ids'][[a,b]];assert aa in sid and bb in sid and tuple(sorted([sid[aa],sid[bb]])) in allowed
                    assert pair_index_by_ids(g,bb,aa)==ei
                    applicable=[di for di in range(len(q['drug_ids'])) if any(np.isin(q['role_'+r][1,q['role_'+r][0]==di],[a,b]).any() for r in ROLES)]
                    edge_scope.append({'context':context,'protein_a':aa,'protein_b':bb,'human_STRING_a':sid[aa],'human_STRING_b':sid[bb],'applicable_query_count':len(applicable),'threshold':700})
                    for mode in ['fixed','delete']:
                        fresh=cache_for(model,g,ei,mode);changed=forward(s,cache=fresh);again=forward(s,cache=cache_for(model,g,ei,mode))
                        repeaterr=max(repeaterr,float(torch.nan_to_num(changed['logits']-again['logits']).abs().max()))
                        untouched=[di for di in range(len(q['drug_ids'])) if di not in applicable]
                        if untouched:assert float(torch.nan_to_num(changed['logits'][untouched]-base[untouched]).abs().max())<=1e-5
                        for di in applicable:record('ppi',di,{'role':'PPI','protein_id':'','protein_a':aa,'protein_b':bb},mode,changed)
                    ppijobs+=len(applicable)
                stability.extend(stability_probe(s,store))
                after={name:numeric_digest(value if isinstance(value,dict) else {'tensor':value}) for name,value in [('g',g),('q',q),('model',model.state_dict()),('cache',s['cache'].protein_h)]};assert before==after
                assert repeaterr<=1e-5 and isolationerr<=1e-5
                df=pd.concat(frame,ignore_index=True)
                globaldf=df.groupby(['kind','context','protocol','mode','class_id']).delta_z.agg(mean_signed='mean',mean_abs=lambda x:x.abs().mean(),finite_interventions='count').reset_index();native_global.extend(globaldf.to_dict('records'))
                consistency.append({'context':context,'reference_logit_error':referr,'original_cache_error':cacheerr,'OOF_score_error':max(errors),'OOF_pairs_checked':len(errors),'role_interventions':rolejobs,'PPI_query_interventions':ppijobs,'repeat_error':repeaterr,'other_query_role_isolation_error':isolationerr,'delete_NA_interventions':finite_delete_NA,'model_graph_query_cache_unchanged':before==after})
                print(context,'roles',rolejobs,'PPI/query',ppijobs,'reference/OOF',referr,max(errors),flush=True)
    for name,data in [('original_outputs.csv',rows),('drug_coverage.csv',scopes),('protein_path_coverage.csv',paths),('absent_paths_NA.csv',absences),('intervention_summary.csv',allsummary),('example_contributions.csv',example_rows),('consistency_checks.csv',consistency),('stability_checks.csv',stability),('train_PPI_scope.csv',edge_scope),('target_scope.csv',target_scope),('global_native_context_PT.csv',native_global)]:pd.DataFrame(data).to_csv(QA/name,index=False,encoding='utf-8-sig')
    verify('policy_commit_before_attribution.json');verify('input_manifest.json');preserved=preserve()
    result={'status':'PASS','models':10,'all_original_outputs':len(rows),'contribution_rows':counts,'prior_files_preserved':preserved,'synthetic_tests_first':True,'guarded_fit_optimizer_backward_calls':len(guard_calls),'WP11_final_closed':False,'WP12':False,'new_training':False,'semantics':'single graph-message perturbation delta logit;NOT SHAP,causality or clinical risk','completed_time_ns':time.time_ns()}
    write_json(QA/'analysis_complete.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try:run()
    except Exception:
        write_json(QA/'failure_evidence.json',{'traceback':traceback.format_exc(),'policy_changed':False,'partial_outputs_retained':True});raise
