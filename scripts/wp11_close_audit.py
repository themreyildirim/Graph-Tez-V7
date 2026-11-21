"""08.11.2026: salt okunur WP11 nihai kapanış; üreticiler çağrılmaz."""
from pathlib import Path
import argparse,json,gzip,re,time
from collections import defaultdict
import numpy as np
import pandas as pd
from wp11_linear_shap import sha,write_json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'reports/qa/WP11/final_closure_v1'
B=ROOT/'reports/qa/WP11/B1_SHAP_v1'
G=ROOT/'reports/qa/WP11/graph_v1'
ROLES=('target','enzyme','transporter','carrier')


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def csv(name,data):pd.DataFrame(data).to_csv(C/name,index=False,encoding='utf-8-sig')


def preserve():
    prior=read(C/'prior_artifacts_sha256.json');bad=[p for p,h in prior.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(prior)


def init():
    if (C/'prior_artifacts_sha256.json').exists():raise RuntimeError('Closure v1 already initialized')
    C.mkdir(parents=True,exist_ok=True);prior={}
    for folder in ['docs','reports','notebooks','scripts','tests','configs','models']:
        for p in sorted((ROOT/folder).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or C in p.parents or p.name.startswith('wp11_close'):continue
            prior[p.relative_to(ROOT).as_posix()]=sha(p)
    for name in ['AGENTS.md','README.md']:prior[name]=sha(ROOT/name)
    write_json(C/'prior_artifacts_sha256.json',prior);(C/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    # Kaynak kimlikleri dışında hiçbir katkı/skor sütunu seçimde okunmaz.
    keys=pd.read_csv(G/'intervention_summary.csv',usecols=['kind','context','drug_id','role','protein_id','protein_a','protein_b','mode'],keep_default_na=False)
    rows=[]
    for context,df in keys[keys['mode'].eq('fixed')].groupby('context',sort=True):
        for kind,role in [('role',r) for r in ROLES]+[('ppi','PPI')]:
            sub=df[df.kind.eq(kind)&df.role.eq(role)].sort_values(['drug_id','protein_id','protein_a','protein_b'])
            if len(sub):rows.append(sub.iloc[0].drop(labels='mode').to_dict())
    csv('replay_keys_frozen.csv',rows)
    write_json(C/'closure_protocol.json',{'date':'2026-11-08','status':'FROZEN_BEFORE_REPLAY','scope':'hash/source/CSV/image consistency;existing method replay only;no new explanations/results',
        'selection':'per context first lexicographic existing typed-role case for each role,and first existing PPI query-pair;fixed+delete;all existing fitted heads',
        'new_method':False,'fit_optimizer_backward':False,'WP12_implementation':False,'accepted_outputs_read_only':True})
    write_json(C/'replay_commit.json',{p.relative_to(ROOT).as_posix():sha(p) for p in [C/'closure_protocol.json',C/'replay_keys_frozen.csv']})
    print('Protected',len(prior),'accepted files;frozen replay keys',len(rows))


def manifests_and_models():
    if (C/'model_integrity_all742.csv').exists():raise RuntimeError('Closure model audit already exists')
    from wp10_molecular_graph import numeric_digest
    rows=[]
    for directory in [B,G]:
        for name in ['prior_artifacts_sha256.json','input_manifest.json','final_artifact_manifest.json']+[('policy_commit_before_explanations.json' if directory==B else 'policy_commit_before_attribution.json')]:
            m=read(directory/name);bad=[];archived=[]
            for p,h in m.items():
                actual=ROOT/p
                if p=='run_status.md':actual=G/'run_status_before.md' if directory==B else C/'run_status_before.md';archived.append(p)
                if not actual.is_file() or sha(actual)!=h:bad.append(p)
            assert not bad,(directory.name,name,bad)
            rows.append({'stage':directory.name,'manifest':name,'verified_entries':len(m),'status':'PASS','archived_mutable_status':bool(archived)})
    csv('manifest_checks.csv',rows)
    models=[]
    for folder in ['WP08_baseline_v1','WP09_PPI_v3_training_v1','WP10_factorial_training_v1']:
        for path in sorted((ROOT/'models'/folder).glob('*.json')):
            md=read(path);p=ROOT/md['parameters_file'];assert sha(p)==md['parameters_sha256']
            with np.load(p,allow_pickle=False) as a:
                data={k:a[k].copy() for k in a.files}
                assert all(np.isfinite(v).all() for v in data.values() if v.dtype.kind in 'fciu')
            numeric=''
            if 'selected_state_sha256' in md:numeric=numeric_digest(data);assert numeric==md['selected_state_sha256']
            models.append({'model_group':folder,'metadata_file':path.relative_to(ROOT).as_posix(),'metadata_sha256':sha(path),'parameters_file':p.relative_to(ROOT).as_posix(),'parameters_sha256':sha(p),'numeric_state_sha256':numeric,'status':'PASS'})
    assert len(models)==742;csv('model_integrity_all742.csv',models)
    print('Manifests verified',len(rows),'model/metadata pairs',len(models),flush=True)


def load_sources():
    contexts=read(G/'frozen_contexts.json');sources={};expected={};absence=[];pathrows=[]
    native=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv');assert native.sequence_available.all()
    role_source=set(map(tuple,native[['drug_id','role','accession']].to_numpy()))
    mapping=pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv');strict=mapping[mapping.strict_taxon_match&mapping.network_taxid.eq(9606)];assert len(strict)==63
    sid=dict(zip(strict.accession,strict.string_id));ppi=pd.read_csv(ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv')
    ppi=ppi[ppi.network_taxid.eq(9606)&ppi.mapping_scope.eq('exact_taxon')&~ppi.score_conflict&ppi.combined_score.ge(700)]
    allowed={tuple(sorted([a,b])) for a,b in zip(ppi.protein1,ppi.protein2)}
    for c in contexts:
        ctx=c['context'];g={};q={}
        for kind,target in [('train',g),('query',q)]:
            with np.load(ROOT/f'reports/qa/WP09/design_v1/folds/{ctx}_{kind}.npz',allow_pickle=False) as a:target.update({k:a[k].copy() for k in a.files})
        assert list(q['drug_ids'])==c['test_ids'] and not set(g['drug_ids'])&set(q['drug_ids']);pool=list(g['protein_ids'])+list(q['unseen_protein_ids']);protocol=ctx.split('_')[0]
        pairset=set()
        for a,b in g['ppi_pairs_700'].T:
            aa,bb=pool[a],pool[b];assert aa in sid and bb in sid and tuple(sorted([sid[aa],sid[bb]])) in allowed;pairset.add((aa,bb))
        for d,drug in enumerate(q['drug_ids']):
            used=set()
            for role in ROLES:
                ids=q['role_'+role][1,q['role_'+role][0]==d]
                if len(ids)==0:absence.append((ctx,protocol,drug,'role',role,'NA_abstain_no_input' if not q['eligible'][d] else 'NA_no_typed_role_relation'))
                for pi in ids:
                    acc=pool[pi];assert (drug,role,acc) in role_source;used.add(int(pi));seen=pi<len(g['protein_ids']);degree=int((g['ppi_pairs_700']==pi).sum()) if seen else 0
                    pathrows.append((ctx,protocol,drug,role,acc,bool(seen),degree,'present' if degree else 'NA_unseen_self_only' if not seen else 'NA_no_incident_train_PPI'))
                    for mode in ['fixed','delete']:expected[('role',ctx,drug,mode,role,acc,'','')]=len(c['fitted_targets'])
            applicable=0
            for a,b in g['ppi_pairs_700'].T:
                if a not in used and b not in used:continue
                applicable+=1
                for mode in ['fixed','delete']:expected[('ppi',ctx,drug,mode,'PPI','',pool[a],pool[b])]=len(c['fitted_targets'])
            if not applicable:absence.append((ctx,protocol,drug,'PPI','','NA_abstain_no_input' if not q['eligible'][d] else 'NA_no_PPI_to_query_role_path'))
        sources[ctx]={'g':g,'q':q,'classes':c['fitted_targets'],'class_bits':{v:1<<i for i,v in enumerate(c['fitted_targets'])},'protocol':protocol}
    na=pd.read_csv(G/'absent_paths_NA.csv',keep_default_na=False);assert set(map(tuple,na.to_numpy()))==set(absence) and len(na)==len(absence)
    p=pd.read_csv(G/'protein_path_coverage.csv');assert set(map(tuple,p.to_numpy()))==set(pathrows) and len(p)==len(pathrows)
    csv('NA_source_consistency.csv',[{'absent_role_PPI_rows':len(absence),'protein_path_rows':len(pathrows),'source_ID_and_path_consistency':'PASS','no_zero_filling':True}])
    return sources,expected


def contributions():
    if (C/'table_audit_complete.json').exists():raise RuntimeError('Closure table audit already exists')
    sources,expected=load_sources();keys=['context','drug_id','mode','role','protein_id','protein_a','protein_b']
    orig=pd.read_csv(G/'original_outputs.csv').set_index(['context','drug_id','class_id']);assert not orig.index.duplicated().any()
    summary=pd.read_csv(G/'intervention_summary.csv',keep_default_na=False).set_index(['kind']+keys)
    cases={};checks=[];example_rows=[];frozen=read(C/'replay_commit.json');assert all(sha(ROOT/p)==h for p,h in frozen.items())
    replay=pd.read_csv(C/'replay_keys_frozen.csv',keep_default_na=False);selected={(r.kind,r.context,r.drug_id,r.role,r.protein_id,r.protein_a,r.protein_b) for r in replay.itertuples()}
    for kind in ['role','ppi']:
        total=0;maxbase=maxdelta=0.;zero=near=NA=0
        for block in pd.read_csv(G/(kind+'_contributions.csv.gz'),chunksize=50000,keep_default_na=False):
            for key in ['role','protein_id','protein_a','protein_b']:assert not block[key].isna().any()
            total+=len(block);ix=pd.MultiIndex.from_frame(block[['context','drug_id','class_id']]);reference=orig.reindex(ix).original_logit.to_numpy();assert np.isfinite(reference).all()
            maxbase=max(maxbase,float(np.abs(reference-block.original_logit.to_numpy()).max()))
            delta=pd.to_numeric(block.delta_z,errors='coerce');alt=pd.to_numeric(block.intervened_logit,errors='coerce');error=np.abs(block.original_logit-alt-delta);maxdelta=max(maxdelta,float(error.max()))
            zero+=int(delta.eq(0).sum());near+=int(delta.abs().le(1e-7).sum());NA+=int(delta.isna().sum())
            assert block.status.eq('OK').all() # accepted v1 has no post-deletion abstention
            for identifiers,b in block.groupby(keys,sort=False,dropna=False):
                key=(kind,)+identifiers;assert key in expected,key
                ctx=identifiers[0];bits=sources[ctx]['class_bits'];assert set(b.class_id)<=set(bits)
                codes=[bits[v] for v in b.class_id];mask=sum(set(codes));assert len(codes)==len(set(codes)),key
                state=cases.setdefault(key,{'bits':0,'n':0,'sum':0.,'abs':0.,'max':0.,'near':0})
                assert state['bits']&mask==0,key;state['bits']|=mask;state['n']+=len(b);state['sum']+=b.delta_z.sum();state['abs']+=b.delta_z.abs().sum();state['max']=max(state['max'],b.delta_z.abs().max());state['near']+=int(b.delta_z.abs().le(1e-7).sum())
                select_key=(kind,identifiers[0],identifiers[1],identifiers[3],identifiers[4],identifiers[5],identifiers[6])
                if select_key in selected:example_rows.append(b.assign(kind=kind))
        assert maxbase<=1e-6 and maxdelta<=1e-5
        checks.append({'kind':kind,'rows':total,'original_logit_CSV_consistency_max_error':maxbase,'delta_identity_max_error':maxdelta,'exact_zero':zero,'near_zero_including_exact':near,'NA_measurement_rows':NA,'all_source_keys_valid':True})
        print('Streamed',kind,total,'rows',flush=True)
    assert set(cases)==set(expected) and len(cases)==len(summary)
    metrics=[]
    for key,state in cases.items():
        n=expected[key];ctx=key[1];assert state['n']==n and state['bits']==(1<<n)-1
        row=summary.loc[key];assert row.PT_count==n
        error=max(abs(state['sum']/n-float(row.mean_signed_delta)),abs(state['abs']/n-float(row.mean_abs_delta)),abs(state['max']-float(row.max_abs_delta)))
        assert error<=1e-5,(key,error);assert state['near']==row.zero_n_abs_tol_1e7
        metrics.append({'kind':key[0],'context':ctx,'drug_id':key[2],'mode':key[3],'role':key[4],'protein_id':key[5],'protein_a':key[6],'protein_b':key[7],'PT_count':n,'unique_complete_CUI_dictionary':True,'summary_max_error':error})
    csv('contribution_stream_checks.csv',checks);csv('all_intervention_key_checks.csv',metrics)
    pd.concat(example_rows,ignore_index=True).to_csv(C/'frozen_replay_existing_rows.csv',index=False,encoding='utf-8-sig')
    networks=read(G/'real_networks.json');example=pd.read_csv(G/'example_contributions.csv',keep_default_na=False);graphchecks=[]
    # JSON → both example CSV and FULL compressed CSV;independent of plotting code.
    wanted={(net['context'],net['drug_id'],net['class_id']) for net in networks};full=[]
    for kind in ['role','ppi']:
        for block in pd.read_csv(G/(kind+'_contributions.csv.gz'),chunksize=50000,keep_default_na=False):
            keep=np.fromiter(((c,d,k) in wanted and mode=='fixed' for c,d,k,mode in zip(block.context,block.drug_id,block.class_id,block['mode'])),dtype=bool,count=len(block))
            if keep.any():full.append(block[keep].assign(kind=kind))
    full=pd.concat(full,ignore_index=True)
    for net in networks:
        ctx=net['context'];drug=net['drug_id'];cui=net['class_id'];s=sources[ctx];assert cui in s['classes']
        f=full[full.context.eq(ctx)&full.drug_id.eq(drug)&full.class_id.eq(cui)]
        assert len(f)==len(net['edges']);used=set();maxerr=0.
        for edge in net['edges']:
            b=f[f.kind.eq(edge['kind'])]
            e=example[example.context.eq(ctx)&example.drug_id.eq(drug)&example.class_id.eq(cui)&example['mode'].eq('fixed')&example.kind.eq(edge['kind'])]
            if edge['kind']=='role':b=b[b.role.eq(edge['role'])&b.protein_id.eq(edge['target'])];e=e[e.role.eq(edge['role'])&e.protein_id.eq(edge['target'])];used.add(edge['target'])
            else:b=b[b.protein_a.eq(edge['source'])&b.protein_b.eq(edge['target'])];e=e[e.protein_a.eq(edge['source'])&e.protein_b.eq(edge['target'])];used.update([edge['source'],edge['target']])
            assert len(b)==len(e)==1;maxerr=max(maxerr,abs(b.delta_z.iloc[0]-edge['delta_z']),abs(e.delta_z.iloc[0]-edge['delta_z']))
        assert used=={n['id'] for n in net['nodes']} and maxerr<=1e-6
        graphchecks.append({'context':ctx,'drug_id':drug,'class_id':cui,'protein_nodes':len(net['nodes']),'role_edges':sum(e['kind']=='role' for e in net['edges']),'PPI_edges':sum(e['kind']=='ppi' for e in net['edges']),'JSON_full_CSV_example_CSV_max_error':maxerr,'status':'PASS'})
    csv('network_data_consistency.csv',graphchecks)
    write_json(C/'table_audit_complete.json',{'status':'PASS','complete_intervention_cases':len(cases),'total_graph_rows':sum(r['rows'] for r in checks),'network_examples_checked':len(networks),'old_outputs_rewritten':False})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['init','manifests','tables','preserve']);a=parser.parse_args()
    if a.stage=='init':init()
    elif a.stage=='manifests':manifests_and_models()
    elif a.stage=='tables':contributions()
    else:print(preserve())
