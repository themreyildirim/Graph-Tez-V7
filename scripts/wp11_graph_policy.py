"""WP11 graph-v1 ön kaydı; gerçek attribution değeri hesaplamaz."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from wp11_linear_shap import sha,write_json
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP11/graph_v1'
ROLES=('target','enzyme','transporter','carrier')


def preserve():
    m=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in m.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(bad)
    return len(m)


def verify(name):
    m=json.loads((QA/name).read_text());assert all(sha(ROOT/p)==h for p,h in m.items()),name
    return len(m)


def init():
    if (QA/'policy_commit_before_attribution.json').exists():raise RuntimeError('Graph policy already frozen')
    QA.mkdir(parents=True,exist_ok=True)
    prior={}
    for folder in ('docs','reports','notebooks','scripts','tests','configs','models'):
        for p in sorted((ROOT/folder).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or QA in p.parents or p.name.startswith(('wp11_graph','test_wp11_graph')):continue
            prior[p.relative_to(ROOT).as_posix()]=sha(p)
    for n in ['AGENTS.md','README.md']:prior[n]=sha(ROOT/n)
    write_json(QA/'prior_artifacts_sha256.json',prior);(QA/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
    policy={'version':'WP11-A1P1-single-message-perturbation-v1','status':'FROZEN_BEFORE_SYNTHETIC_AND_REAL_ATTRIBUTION','models':'all10 frozen selected outer A1P1;primary5 and stress5;no inner models',
        'scope':'all62 test inventory per protocol;eligible61 only receive finite logits;all original fitted PT per context;no missing target filling',
        'primary':'single message masked to0;original degree or role count AND availability masks fixed',
        'sensitivity':'physical undirected PPI pair/typed role relation deletion;remaining degree/count recomputed;last-role deletion also turns off role mask;abstain if all modalities absent',
        'output':'delta_z=original_logit-intervened_logit;signed;not SHAP;not additive decomposition;not clinical risk or causality',
        'ppi':'both directed messages of one canonical strict-human STRING700 train pair together;fresh copied train-cache;never query-to-train edges;single layer limits paths to incident train role proteins',
        'role':'query drug-protein typed relation only;target/enzyme/transporter/carrier kept separate;protein features/node retained',
        'absence':'missing role/PPI computational path,unseen-self-only protein or abstention => NA reason;never zero-filled;existing applicable edge with zero measured delta stays0',
        'PT_global':'native context perPT only;edge summaries over that context fitted PT explicitly;no cross-fold CUI union filling',
        'examples':'each context first2 lexicographic eligible test drug IDs plus DB00199 Erythromycin if heldout;first2 lexicographic fitted CUIs;no test labels/performance/logit ranking selection',
        'plots':'primary first lexicographic test example and primary heldout Erythromycin;first fitted CUI;whole query role neighborhood and incident train-PPI edges;no highest-effect selection',
        'stability':'exact repeat;canonical pair endpoint order;protein/query/edge-order permutation;separate deletion-vs-mask sensitivity is not statistical stability/CI;frozen-weight local result,not retraining uncertainty',
        'runtime':'CPU float32 saved model eval,no_grad;1 thread deterministic;OOF tolerance1e-7;logit/reference/order tolerance1e-5;zero convention abs(delta)<=1e-7;raw deltas retained',
        'technical_gate':'synthetic analytic tests BEFORE any real attribution;full zero-intervention matches accepted encoder;guards against all training/optimizer',
        'state':'original model/train/query/cache immutable;separate intervention tensors;fresh PPI cache includes model+graph+mask identity,not spoofed old cache',
        'QC':'62/1061/6416;54/8atom mask;Methenamine abstains;Tobramycin missing protein;no context80,no K12 mixing',
        'new_training':False,'WP12':False}
    write_json(QA/'policy_v1.json',policy)
    inputs={};contexts=[];examples=[];membership=[];pathcounts=[]
    for protocol in ['primary','stress']:
        for fold in range(1,6):
            context=f'{protocol}_o{fold:02}_final';mdp=ROOT/f'models/WP10_factorial_training_v1/{context}_A1P1.json';md=json.loads(mdp.read_text())
            paths=[mdp,ROOT/md['parameters_file']]+[ROOT/f'reports/qa/WP09/design_v1/folds/{context}_{k}.npz' for k in ['train','query']]
            assert sha(paths[1])==md['parameters_sha256'] and md['variant']=='A1P1' and md['status']=='OK'
            for p in paths:inputs[p.relative_to(ROOT).as_posix()]=sha(p)
            with np.load(paths[2],allow_pickle=False) as a:g={k:a[k] for k in a.files}
            with np.load(paths[3],allow_pickle=False) as a:q={k:a[k] for k in a.files}
            ids=sorted(q['drug_ids'][q['eligible']].tolist());picked=sorted(set(ids[:2]+(['DB00199'] if 'DB00199' in ids else [])))
            for d in picked:
                for cui in sorted(md['fitted_targets'])[:2]:examples.append({'context':context,'protocol':protocol,'outer_fold':fold,'drug_id':d,'class_id':cui,'selection':'lexicographic plus predeclared Erythromycin;no outcome or performance'})
            contexts.append({'context':context,'model_file':paths[1].relative_to(ROOT).as_posix(),'metadata_file':mdp.relative_to(ROOT).as_posix(),'test_ids':q['drug_ids'].tolist(),'eligible_ids':ids,'fitted_targets':md['fitted_targets'],'declared_targets':md['declared_train_targets'],'train_drug_ids':g['drug_ids'].tolist(),'train_protein_ids':g['protein_ids'].tolist(),'unseen_query_protein_ids':q['unseen_protein_ids'].tolist()})
            for d in g['drug_ids']:membership.append({'context':context,'drug_id':d,'scope':'TRAIN'})
            for i,d in enumerate(q['drug_ids']):
                membership.append({'context':context,'drug_id':d,'scope':'TEST' if q['eligible'][i] else 'TEST_ABSTAIN'})
                pool=set()
                for role in ROLES:pool.update(q['role_'+role][1,q['role_'+role][0]==i].tolist())
                touch=sum(a in pool or b in pool for a,b in g['ppi_pairs_700'].T)
                pathcounts.append({'context':context,'protocol':protocol,'drug_id':d,'eligible':bool(q['eligible'][i]),'role_links':sum(int((q['role_'+r][0]==i).sum()) for r in ROLES),'train_PPI_pairs':g['ppi_pairs_700'].shape[1],'applicable_incident_PPI_pairs':touch})
    for p in [ROOT/'docs/plan/WP11_A1P1_GRAPH_EXPLANATION_CONTRACT_v1.md',ROOT/'AGENTS.md',ROOT/'docs/plan/ROADMAP_V7.md',ROOT/'reports/qa/WP10/training_v1/oof_predictions.csv',ROOT/'reports/qa/WP10/encoder_v1/molecule_registry.json',ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv',ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv',ROOT/'reports/qa/WP06/protein_string_mapping.csv']:
        inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    reg=json.loads((ROOT/'reports/qa/WP10/encoder_v1/molecule_registry.json').read_text())
    for m in reg.values():p=ROOT/m['graph_file'];inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    write_json(QA/'frozen_contexts.json',contexts);write_json(QA/'input_manifest.json',inputs)
    for name,rows in [('examples_frozen.csv',examples),('membership_frozen.csv',membership),('path_scope_before_attribution.csv',pathcounts)]:pd.DataFrame(rows).to_csv(QA/name,index=False,encoding='utf-8-sig')
    files=['policy_v1.json','frozen_contexts.json','input_manifest.json','examples_frozen.csv','membership_frozen.csv','path_scope_before_attribution.csv']
    write_json(QA/'policy_commit_before_attribution.json',{(QA/f).relative_to(ROOT).as_posix():sha(QA/f) for f in files})
    print('Frozen before attribution',len(contexts),'models',len(examples),'examples',len(prior),'prior files')


if __name__=='__main__':init()
