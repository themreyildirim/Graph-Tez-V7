"""Kullanıcı onaylı WP10 dört kollu gerçek eğitim; outer test yalnız ayrı score aşamasında."""
from pathlib import Path
import argparse,copy,hashlib,json,math,platform,time,traceback
import numpy as np
import pandas as pd
import torch
from torch import nn
from wp10_molecular_encoder import initialized_model,VARIANTS,load_context
from wp10_molecular_graph import load_store
from wp10_training_forward import prepare,input_digest,train_forward,query_forward
from wp09_data import validate_bundle
from wp08_baseline_metrics import RankingCache

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP10/training_v1'
MODEL=ROOT/'models/WP10_factorial_training_v1'
NULL=ROOT/'reports/qa/WP09/null_gate_v3'
PREP=ROOT/'reports/qa/WP08/experimental_preparation'
VERSION='WP10-molecular-protein-factorial-observed-record-training-v1'
SEMANTICS='Observed SIDER record ranking proxy; unknown NOT verified biological negative; NOT clinical risk; molecular/protein GNN factorial exploratory study'
NAMES=VARIANTS


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write_json(path,obj):
    def clean(v):
        if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [clean(x) for x in v]
        if isinstance(v,np.generic):return clean(v.item())
        if isinstance(v,float) and not math.isfinite(v):return None
        return v
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def csv(name,frame):frame.to_csv(QA/name,index=False,encoding='utf-8-sig',lineterminator='\n')


def preserve():
    previous=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(f'Accepted output changed: {bad}')
    return len(previous)


def initialize():
    QA.mkdir(parents=True,exist_ok=True)
    if (QA/'run_config.json').exists():raise RuntimeError('Training v1 already frozen')
    previous={}
    for folder in ('docs','reports','notebooks','scripts','tests','configs','models'):
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or QA in path.parents or MODEL in path.parents:continue
            if path.name.startswith(('wp10_train','test_wp10_train')):continue
            previous[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ('AGENTS.md','README.md'):previous[name]=sha(ROOT/name)
    write_json(QA/'prior_outputs_sha256.json',previous)
    previous_decisions=json.loads((ROOT/'reports/qa/WP09/training_v1/outer_fit_and_selection.json').read_text(encoding='utf-8'))
    jobs0=pd.read_csv(NULL/'training_sequence_PREVIEW_ONLY.csv',keep_default_na=False)
    rows=[]
    for job in jobs0[jobs0.variant.eq('G_noPPI')].to_dict('records'):
        for variant in NAMES:rows.append({**job,'variant':variant,'null_replicate':-1,'null_file':'','status':'AUTHORIZED_NOT_RUN'})
    jobs=pd.DataFrame(rows);assert len(jobs)==152
    csv('training_jobs_frozen.csv',jobs)
    run={'version':VERSION,'user_authorized_training':True,'authorization_date':'2026-11-07',
        'authorization':'Current user explicitly approves WP10 real four-arm training; NO shuffled experiments; WP11 not authorized',
        'models':list(NAMES),'shuffled_PPI':False,'seed_base':20261106,'threshold':700,
        'architecture':'accepted WP10 MolecularProteinFusion 5512+151*K;44/14 features;16 hidden;8 molecular;150 fusion',
        'optimizer':{'name':'AdamW','lr':.001,'weight_decay':.001},'loss':'mean BCEWithLogitsLoss observed-record proxy, no weights',
        'epochs':{'max':200,'patience':20,'min_delta':.0001,'outer':'floor(median(common inner best epochs)+0.5), each model'},
        'initial_common_inner_from_WP09':previous_decisions,'minimum_common_inner':2,
        'additional_failure_policy':'common finite/evaluable inner intersection across4;min2;any failed outer fit makes whole four-arm primary outer NA;no low-score exclusions',
        'runtime':{'dtype':'float32','CPU_threads':1,'deterministic':True,'full_batch':True,
            'prepared_forward':'same accepted layers/equations, fixed data validated once per fit; reference output/gradient equivalence tests required'},
        'targets':'frozen B2 train-only fittable PT;source1061;unknown NOT verified biological negative',
        'QC':'62 inventory,61 input eligibility,54 atom-QC masks;8 closed;Methenamine abstention;no context80/K12 PPI',
        'evaluation_before_results':{'scopes':['paired54','own61'],'primary':'drug_macro_AP','secondary':['micro_AP','within_fold_class_macro_AUROC'],
            'pooled_class_AUROC':'diagnostic only','bootstrap_reps':1000,'bootstrap_min_valid':800,'seed':'20261106+9000+protocol_index',
            'unit':'same frozen structural groups and draws for all models;fixed-OOF conditional;not external validation',
            'contrasts':{'atom_P0':{'A1P0':1,'A0P0':-1},'atom_P1':{'A1P1':1,'A0P1':-1},
                'PPI_A0':{'A0P1':1,'A0P0':-1},'PPI_A1':{'A1P1':1,'A1P0':-1},
                'interaction':{'A1P1':1,'A0P1':-1,'A1P0':-1,'A0P0':1},
                'marginal_atom':{'A1P0':.5,'A0P0':-.5,'A1P1':.5,'A0P1':-.5},
                'marginal_PPI':{'A0P1':.5,'A0P0':-.5,'A1P1':.5,'A1P0':-.5}},
            'example':'alphabetically smallest primary paired54 drug ID;all4 model rankings;no result-based example choice',
            'references':'fixed B0/B1/B2 and WP09 no/real PPI only;no refits'},
        'semantics':SEMANTICS,'WP11':False}
    write_json(QA/'run_config.json',run)
    selected={p:h for p,h in previous.items() if p.startswith(('reports/qa/WP10/encoder_v1/','reports/qa/WP09/design_v1/folds/',
        'reports/qa/WP08/experimental_preparation/')) or p in ['reports/qa/WP03/drug_pt_positives.csv','scripts/wp10_molecular_encoder.py',
        'scripts/wp10_molecular_graph.py','scripts/wp09_encoder.py','reports/qa/WP09/null_gate_v3/training_preview_sources.json',
        'reports/qa/WP09/training_v1/outer_fit_and_selection.json']}
    write_json(QA/'input_manifest.json',selected);MODEL.mkdir(exist_ok=True)
    print(f'Frozen WP10 four-arm contract;152 fits;{len(previous)} prior files protected',flush=True)


def configure_runtime():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)


def load_bundle(context,kind):
    path=ROOT/f'reports/qa/WP09/design_v1/folds/{context}_{kind}.npz'
    with np.load(path,allow_pickle=False) as archive:return {k:archive[k] for k in archive.files}


def source_labels():
    frame=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','meddra_cui','conservative'])
    return frame[frame.conservative][['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'class_id'})


def restrict_labels(source,ids):
    ids=list(ids);frame=source[source.drug_id.isin(ids)]
    if frame.duplicated(['drug_id','class_id']).any():raise ValueError('Duplicate source positive')
    return {d:set(frame[frame.drug_id.eq(d)].class_id) for d in ids}


def proxy_matrix(labels,ids,targets):
    if set(labels)!=set(ids):raise ValueError('Label API requires exactly requested train/validation IDs, no heldout IDs')
    return np.asarray([[int(c in labels[d]) for c in targets] for d in ids],dtype=np.float32)


def select_query(query,selected_ids,train_protein_count):
    selected_ids=list(selected_ids);index={d:i for i,d in enumerate(query['drug_ids'])}
    if set(selected_ids)-set(index):raise ValueError('Requested query ID absent')
    indices=[index[d] for d in selected_ids];old_to_new={old:new for new,old in enumerate(indices)}
    role_raw={r:query['role_'+r][:,np.isin(query['role_'+r][0],indices)] for r in ('target','enzyme','transporter','carrier')}
    used=sorted({int(p-train_protein_count) for edges in role_raw.values() for p in edges[1] if p>=train_protein_count})
    remap={train_protein_count+old:train_protein_count+new for new,old in enumerate(used)}
    result={k:query[k][indices].copy() for k in ('drug_ids','chemistry','masks','eligible','split')}
    result['unseen_protein_ids']=query['unseen_protein_ids'][used].copy()
    result['unseen_protein_x']=query['unseen_protein_x'][used].copy()
    for role,edges in role_raw.items():
        result['role_'+role]=np.asarray([(old_to_new[int(d)],int(p) if p<train_protein_count else remap[int(p)]) for d,p in edges.T],dtype=np.int64).reshape(-1,2).T
    return result


def state_hash(state):
    h=hashlib.sha256()
    for name,value in sorted(state.items()):
        array=value.detach().cpu().contiguous().numpy();h.update(name.encode());h.update(str(array.dtype).encode());h.update(str(array.shape).encode());h.update(array.tobytes())
    return h.hexdigest()


def drug_ap(y,scores):
    values=[]
    for yy,ss in zip(y,scores):values.append(RankingCache(yy,ss,np.zeros(len(yy),dtype=int)).evaluate(np.ones(1))[0][0])
    values=np.asarray(values);return float(values[np.isfinite(values)].mean()) if np.isfinite(values).any() else float('nan')


def fit_model(graph,train_labels,targets,variant,seed,null_pairs=None,validation=None,validation_labels=None,
              fixed_epochs=None,max_epochs=200,patience=20,min_delta=.0001,store=None):
    """No outer-test label/value argument; exact train/validation labels only."""
    if variant not in NAMES or null_pairs is not None:raise ValueError('Only four approved arms;no null edges')
    configure_runtime();ids=list(graph['drug_ids']);eligible=np.asarray(graph['eligible'],bool);fit_ids=list(np.asarray(ids)[eligible])
    if not targets or not fit_ids:raise ValueError('NA_no_trainable_targets_or_drugs')
    if len(set(targets))!=len(targets):raise ValueError('Duplicate PT target')
    y=proxy_matrix(train_labels,fit_ids,targets)
    if not ((y.sum(0)>0)&(y.sum(0)<len(y))).all():raise ValueError('Single train proxy outcome;no fallback')
    if validation is not None:
        validate_bundle(graph,validation)
        if not np.all(validation['split']=='validation'):raise ValueError('Only validation queries may select epochs')
        ve=validation['eligible'];val_ids=list(validation['drug_ids'][ve]);yv=proxy_matrix(validation_labels,val_ids,targets)
    elif fixed_epochs is None:raise ValueError('Outer fit requires committed fixed epochs')
    else:validate_bundle(graph)
    store=get_store() if store is None else store
    model=initialized_model(int(seed),num_targets=len(targets));initial=copy.deepcopy(model.state_dict());initial_hash=state_hash(initial)
    train_input=prepare(model,graph,store.make_batch(ids))
    val_input=prepare(model,validation,store.make_batch(validation['drug_ids'])) if validation is not None else None
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
    history=[];events=[];best_state=None;best_ap=-math.inf;best_epoch=None;bad=0;steps=0;status='OK';error=''
    handle=model.base.protein.message.register_forward_pre_hook(lambda module,args:events.append(float(args[0].detach().norm())))
    limit=int(fixed_epochs if fixed_epochs is not None else max_epochs)
    try:
        for epoch in range(1,limit+1):
            model.train();optimizer.zero_grad(set_to_none=True)
            output=train_forward(model,train_input,variant);logits=output['logits'][eligible]
            if not torch.isfinite(logits).all():raise FloatingPointError('Nonfinite train logits')
            loss=nn.functional.binary_cross_entropy_with_logits(logits,torch.from_numpy(y),reduction='none').mean(1).mean()
            if not torch.isfinite(loss):raise FloatingPointError('Nonfinite proxy loss')
            input_norm=events[-1];loss.backward()
            def grad(p):return float(p.grad.norm()) if p.grad is not None else 0.
            pg=grad(model.base.protein.message.weight);ag=grad(model.molecular.atom_message.weight);bg=grad(model.molecular.bond_message.weight)
            if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):raise FloatingPointError('Nonfinite gradient')
            optimizer.step();steps+=1
            if any(not torch.isfinite(p).all() for p in model.parameters()):raise FloatingPointError('Nonfinite updated parameters')
            ap=vl=float('nan');nval=0
            if validation is not None:
                model.eval()
                with torch.no_grad():
                    cache=train_forward(model,train_input,variant)['protein_h']
                    pred=query_forward(model,val_input,cache,variant)['logits'][ve]
                    if not torch.isfinite(pred).all():raise FloatingPointError('Nonfinite validation logits')
                    ap=drug_ap(yv,torch.sigmoid(pred).numpy());vl=float(nn.functional.binary_cross_entropy_with_logits(pred,torch.from_numpy(yv)))
                    nval=int(((yv.sum(1)>0)&(yv.sum(1)<yv.shape[1])).sum())
                if math.isfinite(ap) and (best_epoch is None or ap>best_ap+min_delta):
                    best_ap=ap;best_epoch=epoch;best_state=copy.deepcopy(model.state_dict());bad=0
                else:bad+=1
            history.append({'epoch':epoch,'train_BCE_pre_update':float(loss.detach()),'validation_BCE_post_update':vl,
                'validation_drug_AP':ap,'validation_AP_evaluable_drugs':nval,'message_weight_gradient_norm':pg,
                'atom_message_gradient_norm':ag,'bond_message_gradient_norm':bg,'train_message_input_norm':input_norm,'optimizer_steps_cumulative':steps})
            if validation is not None and bad>=patience:break
        terminal_hash=state_hash(model.state_dict())
        if validation is not None:
            if best_state is None:status='NA_validation_not_evaluable'
            else:model.load_state_dict(best_state)
        else:best_epoch=limit;best_ap=float('nan')
    except Exception:status='NA_fit_exception';error=traceback.format_exc();terminal_hash=state_hash(model.state_dict())
    finally:handle.remove()
    assert input_digest(train_input.graph,train_input.molecules)==train_input.digest
    if val_input is not None:assert input_digest(val_input.graph,val_input.molecules)==val_input.digest
    state=model.state_dict()
    def delta(prefix=''):return math.sqrt(sum(float(((state[k]-initial[k]).double()**2).sum()) for k in state if k.startswith(prefix)))
    info={'status':status,'error':error,'initial_state_sha256':initial_hash,'selected_state_sha256':state_hash(state),
        'terminal_state_sha256':terminal_hash,'best_epoch':best_epoch,'best_validation_AP':best_ap,'epochs_run':len(history),'optimizer_steps':steps,
        'selected_state_L2_change':delta(),'molecular_state_L2_change':delta('molecular.'),
        'maximum_message_gradient_norm':max((r['message_weight_gradient_norm'] for r in history),default=0.),
        'maximum_atom_message_gradient_norm':max((r['atom_message_gradient_norm'] for r in history),default=0.),
        'maximum_bond_message_gradient_norm':max((r['bond_message_gradient_norm'] for r in history),default=0.),
        'maximum_train_message_input_norm':max((r['train_message_input_norm'] for r in history),default=0.),
        'train_fit_drug_ids':fit_ids,'declared_graph_train_drug_ids':ids,'train_observed_positive':int(y.sum()),
        'train_unknown_proxy_NOT_negative':int(y.size-y.sum()),'num_targets':len(targets),
        'validation_query_ids':list(validation['drug_ids']) if validation is not None else [],
        'actual_validation_feature_proteins':list(validation['unseen_protein_ids']) if validation is not None else [],
        'train_molecule_ids':ids,'validation_molecule_ids':list(validation['drug_ids']) if validation is not None else [],
        'prepared_train_input_sha256':train_input.digest,'parameter_count':sum(p.numel() for p in model.parameters()),'dtype':'float32','semantics':SEMANTICS}
    return model,pd.DataFrame(history),info


_STORE=None
def get_store():
    global _STORE
    if _STORE is None:_STORE=load_store()
    return _STORE


def job_key(job):return f'{job["context"]}_{job["variant"]}'+(f'_R{int(job["null_replicate"])}' if int(job['null_replicate'])>=0 else '')


def display_name(job):return job['variant']+(f'_R{int(job["null_replicate"])}' if int(job['null_replicate'])>=0 else '')


def context_arguments(job,source):
    graph=load_bundle(job['context'],'train');query=load_bundle(job['context'],'query');validate_bundle(graph,query)
    sources=json.loads((NULL/'training_preview_sources.json').read_text(encoding='utf-8'))[job['context']]
    targets=sources['fittable_train_B2_PT'];fit_ids=sources['fit_eligible_train_ids']
    null=None
    if job['variant']=='G_shuffledPPI':
        with np.load(ROOT/job['null_file'],allow_pickle=False) as archive:null=archive['ppi_pairs'].copy()
    val=None;val_labels=None
    if int(job['inner_fold'])>0:
        validation_ids=list(query['drug_ids'][query['split']=='validation'])
        val=select_query(query,validation_ids,len(graph['protein_ids']))
        val_labels=restrict_labels(source,list(val['drug_ids'][val['eligible']]))
    return graph,query,targets,null,val,restrict_labels(source,fit_ids),val_labels,sources


def run_job(job,source,fixed_epochs=None):
    key=job_key(job);path=MODEL/(key+'.json')
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    base={'job_key':key,'context':job['context'],'protocol':job['protocol'],'outer_fold':int(job['outer_fold']),
        'inner_fold':int(job['inner_fold']),'variant':job['variant'],'model':display_name(job),'null_replicate':int(job['null_replicate']),
        'seed':int(job['init_seed']),'model_version':VERSION,'semantics':SEMANTICS,'threshold':700,
        'identity_and_target_scope_sha256':job['identity_and_target_scope_sha256'],
        'training_graph_file':job['training_graph_file'],'training_graph_sha256':sha(ROOT/job['training_graph_file']),
        'query_file_sha256':sha(ROOT/job['query_file']),'fixed_outer_epochs':fixed_epochs,'molecular_atom_bond_GNN':True,
        'approved_run_config_sha256':sha(QA/'run_config.json')}
    started=time.perf_counter()
    try:
        graph,query,targets,null,val,train_labels,val_labels,sources=context_arguments(job,source)
        model,history,info=fit_model(graph,train_labels,targets,job['variant'],int(job['init_seed']),null,val,val_labels,fixed_epochs)
        param_path=MODEL/(key+'.npz')
        np.savez_compressed(param_path,**{k:v.detach().cpu().numpy() for k,v in model.state_dict().items()})
        csv('history/'+key+'.csv',history)
        md={**base,**info,'fitted_targets':targets,'declared_train_targets':sources['declared_train_B2_PT'],
            'parameters_file':param_path.relative_to(ROOT).as_posix(),'parameters_sha256':sha(param_path),
            'protein_ids':list(graph['protein_ids']),'protein_transform_source':'frozen WP08 context statistics; no refit',
            'null_file':job['null_file'],'null_file_sha256':sha(ROOT/job['null_file']) if job['null_file'] else '',
            'source_sidecar':sources,'elapsed_seconds':time.perf_counter()-started,
            'effective_directed_PPI_columns':0 if job['variant'].endswith('0') else 2*(null.shape[1] if null is not None else graph['ppi_pairs_700'].shape[1])}
    except Exception:md={**base,'status':'NA_job_exception','error':traceback.format_exc(),'elapsed_seconds':time.perf_counter()-started}
    write_json(path,md)
    return md


def training():
    preserve();run=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))
    if not run['user_authorized_training']:raise RuntimeError('Training not authorized')
    if (QA/'training_complete.json').exists():raise RuntimeError('WP10 v1 completed; no result-driven refit')
    (QA/'history').mkdir(exist_ok=True);configure_runtime();jobs=pd.read_csv(QA/'training_jobs_frozen.csv',keep_default_na=False)
    source=source_labels();trace=[];outer_decisions=[]
    for protocol in ('primary','stress'):
        for fold in range(1,6):
            local=jobs[jobs.protocol.eq(protocol)&jobs.outer_fold.eq(fold)]
            inner=[]
            for job in local[local.inner_fold.gt(0)].to_dict('records'):
                md=run_job(job,source);inner.append(md);trace.append(md)
            common=[]
            for inner_fold in sorted(local[local.inner_fold.gt(0)].inner_fold.unique()):
                group=[m for m in inner if m['inner_fold']==inner_fold]
                if len(group)==4 and all(m['status']=='OK' and m.get('best_validation_AP') is not None and math.isfinite(m['best_validation_AP']) for m in group):common.append(int(inner_fold))
            decision={'protocol':protocol,'outer_fold':fold,'actual_common_inner_folds':common,'common_inner_count':len(common),
                'status':'SELECTION_COMPLETE' if len(common)>=2 else 'NA_selection_insufficient','outer_epoch_by_model':{},
                'outer_test_labels_or_scores_used':False}
            if len(common)>=2:
                for job in local[local.inner_fold.eq(0)].to_dict('records'):
                    name=display_name(job);epochs=[m['best_epoch'] for m in inner if m['model']==name and m['inner_fold'] in common]
                    decision['outer_epoch_by_model'][name]=int(math.floor(float(np.median(epochs))+.5))
            # Per outer commit precedes all outer final fits and any outer scoring.
            write_json(QA/f'selections/{protocol}_o{fold:02}.json',decision)
            if len(common)>=2:
                outer=[run_job(job,source,decision['outer_epoch_by_model'][display_name(job)]) for job in local[local.inner_fold.eq(0)].to_dict('records')]
                trace.extend(outer);decision['outer_all_four_fit_OK']=len(outer)==4 and all(m['status']=='OK' for m in outer)
            else:decision['outer_all_four_fit_OK']=False
            outer_decisions.append(decision)
            write_json(QA/'fit_progress.json',{'last_protocol':protocol,'last_outer_fold':fold,'model_jobs_recorded':len(trace),'outer_test_scoring':False})
            print(f'WP10 {protocol} outer{fold}: common inner={common}; outer epochs={decision["outer_epoch_by_model"]}; all four fit OK={decision["outer_all_four_fit_OK"]}',flush=True)
    summary=pd.DataFrame([{k:m.get(k) for k in ('job_key','context','protocol','outer_fold','inner_fold','model','seed','status','best_epoch','best_validation_AP',
        'epochs_run','optimizer_steps','selected_state_L2_change','maximum_message_gradient_norm','maximum_atom_message_gradient_norm','maximum_bond_message_gradient_norm','molecular_state_L2_change','maximum_train_message_input_norm','initial_state_sha256','selected_state_sha256','num_targets','train_observed_positive','train_unknown_proxy_NOT_negative','parameter_count','elapsed_seconds')} for m in trace])
    csv('model_fit_summary.csv',summary);write_json(QA/'outer_fit_and_selection.json',outer_decisions)
    selections={p.relative_to(ROOT).as_posix():sha(p) for p in (QA/'selections').glob('*.json')}
    write_json(QA/'selection_complete_before_test_scoring.json',{'selections':selections,'outer_test_scoring_performed':False,
        'outer_epoch_decisions_sha256':sha(QA/'outer_fit_and_selection.json')})
    write_json(QA/'model_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in MODEL.glob('*') if p.is_file()})
    write_json(QA/'training_complete.json',{'version':VERSION,'jobs_recorded':len(trace),'optimizer_steps':int(summary.optimizer_steps.fillna(0).sum()),
        'fit_status_counts':summary.status.value_counts().to_dict(),'outer_complete_count':sum(d['outer_all_four_fit_OK'] for d in outer_decisions),
        'source_positives':len(source),'source_drugs':source.drug_id.nunique(),'source_PT':source.class_id.nunique(),
        'outer_test_scores_produced':False,'prior_files_verified':preserve(),'semantics':SEMANTICS})


def restore(md):
    configure_runtime();torch.manual_seed(md['seed']);model=initialized_model(md['seed'],num_targets=len(md['fitted_targets']))
    with np.load(ROOT/md['parameters_file'],allow_pickle=False) as source:model.load_state_dict({k:torch.from_numpy(source[k].copy()) for k in source.files})
    model.eval();return model


def score_queries(md,graph,query,null=None):
    if null is not None:raise ValueError('No WP10 shuffled experiment')
    model=restore(md);before=state_hash(model.state_dict());store=get_store()
    ti=prepare(model,graph,store.make_batch(graph['drug_ids']));qi=prepare(model,query,store.make_batch(query['drug_ids']))
    with torch.no_grad():
        cache=train_forward(model,ti,md['variant'])['protein_h'];saved=cache.clone()
        scores=torch.sigmoid(query_forward(model,qi,cache,md['variant'])['logits']).numpy()
    if before!=state_hash(model.state_dict()) or not torch.equal(cache,saved):raise AssertionError('Query changed model/train state')
    return scores


def scoring():
    preserve()
    if not (QA/'training_complete.json').exists():raise RuntimeError('Complete all selection/training before outer score')
    if (QA/'scoring_complete.json').exists():raise RuntimeError('Outer v1 scores already frozen')
    committed=json.loads((QA/'selection_complete_before_test_scoring.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in committed['selections'].items())
    decisions=json.loads((QA/'outer_fit_and_selection.json').read_text(encoding='utf-8'))
    jobs=pd.read_csv(QA/'training_jobs_frozen.csv',keep_default_na=False)
    # Test outcomes are accessed only now, after frozen inner selections and completed outer weights.
    source=source_labels();pred=[];status=[]
    for decision in decisions:
        local=jobs[jobs.protocol.eq(decision['protocol'])&jobs.outer_fold.eq(decision['outer_fold'])&jobs.inner_fold.eq(0)]
        for job in local.to_dict('records'):
            graph=load_bundle(job['context'],'train');query=load_bundle(job['context'],'query')
            query=select_query(query,list(query['drug_ids'][query['split']=='test']),len(graph['protein_ids']))
            name=display_name(job);md_path=MODEL/(job_key(job)+'.json')
            md=json.loads(md_path.read_text(encoding='utf-8')) if md_path.exists() else None
            scores=None
            if decision['outer_all_four_fit_OK']:
                null=None
                if job['null_file']:
                    with np.load(ROOT/job['null_file'],allow_pickle=False) as archive:null=archive['ppi_pairs'].copy()
                scores=score_queries(md,graph,query,null)
            labels=restrict_labels(source,list(query['drug_ids']))
            for i,drug in enumerate(query['drug_ids']):
                s='ABSTAIN_no_input' if not query['eligible'][i] else 'SCORED' if scores is not None else 'NA_outer_primary_fit_or_selection'
                status.append({'protocol':job['protocol'],'outer_fold':job['outer_fold'],'model':name,'drug_id':drug,'status':s,'semantics':SEMANTICS})
                if s!='SCORED':continue
                if not np.isfinite(scores[i]).all():raise FloatingPointError('Outer scores nonfinite for eligible query')
                for c,value in zip(md['fitted_targets'],scores[i]):pred.append({'protocol':job['protocol'],'outer_fold':int(job['outer_fold']),
                    'model':name,'drug_id':drug,'class_id':c,'observed_record_s':int(c in labels[drug]),'score_observed_record_proxy':float(value),
                    'model_job_key':job_key(job),'outer_epochs':md['best_epoch'],'model_version':VERSION,'semantics':SEMANTICS})
    csv('oof_predictions.csv',pd.DataFrame(pred));csv('prediction_status_all62.csv',pd.DataFrame(status))
    write_json(QA/'scoring_complete.json',{'predictions':len(pred),'selection_commit_sha256':sha(QA/'selection_complete_before_test_scoring.json'),
        'outer_decisions_sha256_unchanged':sha(QA/'outer_fit_and_selection.json'),'model_manifest_sha256':sha(QA/'model_artifact_manifest.json'),
        'predictions_sha256':sha(QA/'oof_predictions.csv'),'model_refit_during_scoring':False,'prior_files_verified':preserve()})
    print(f'Frozen outer scoring complete: {len(pred)} pairs; no refit',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['init','train','score','preserve'])
    action=parser.parse_args().action
    if action=='init':initialize()
    elif action=='train':training()
    elif action=='score':scoring()
    else:print(preserve())
