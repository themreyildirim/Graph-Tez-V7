"""WP09 son null kapısı: topoloji-only replay, sabit üç null ve ortak inner kapsam.

Model/etiket/optimizer bağımlılığı yoktur. Eski üreticiler ve artefaktlar değiştirilmez.
"""
from pathlib import Path
from collections import Counter
import copy,json,hashlib,math
import numpy as np
import pandas as pd
from wp09_shuffle import shuffle_pairs,edge_hash

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP09/null_gate_v3'
DESIGN=ROOT/'reports/qa/WP09/design_v1'
CONFIG=ROOT/'configs/WP09_training_PROPOSED_v3.json'


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def write_csv(name,frame):frame.to_csv(QA/name,index=False,encoding='utf-8-sig',lineterminator='\n')


def preserve():
    previous=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(f'Prior output changed: {bad}')
    return len(previous)


def snapshot():
    QA.mkdir(parents=True,exist_ok=True)
    if (QA/'prior_outputs_sha256.json').exists():raise RuntimeError('Null gate snapshot already exists')
    previous={}
    new_names={'WP09_training_PROPOSED_v3.json','WP09_null_policy_review.ipynb'}
    for folder in ('docs','reports','notebooks','scripts','tests','configs','models'):
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or 'null_gate_v3' in path.parts:continue
            if path.name in new_names or path.name.lower().startswith(('wp09_null_','test_wp09_null_')):continue
            previous[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ('AGENTS.md','README.md'):previous[name]=sha(ROOT/name)
    write_json(QA/'prior_outputs_sha256.json',previous)
    print(f'Frozen null-gate preservation snapshot: {len(previous)} files',flush=True)


def freeze_proposal():
    v2_path=ROOT/'configs/WP09_training_PROPOSED_v2.json'
    proposal=copy.deepcopy(json.loads(v2_path.read_text(encoding='utf-8')))
    proposal.update(version='WP09-training-PROPOSED-v3',status='AWAITING_EXPLICIT_TRAINING_APPROVAL',training_enabled=False,
        scope_now='null policy and common-scope preflight only; no model construction/fit/optimizer/PT scores')
    proposal['previous_proposal_sha256']=sha(v2_path)
    proposal['revision_basis']='Preserve generator/seeds/0.5 criterion; specify three fixed null replicates and shared inner/outer NA rules before new preflight outcomes'
    proposal['threshold']={'recommended_primary':700,'approved_primary':None,'sensitivities':[400,900],
        'sensitivity_status':'deferred; not part of first WP09 primary fit request','reason':'user-retained topology/null-feasibility proposal; not predictive optimization'}
    proposal['shuffle'].update({'algorithm':'unchanged wp09_shuffle.shuffle_pairs, accepted double-edge switches',
        'replicates':3,'replicate_indices':[0,1,2],'replicate_seed_formula':'base + 10000 + 100*sorted_context_index + 700 + 1000000*replicate_index',
        'same_original_start_each_replicate':True,'retry_or_best_replica_selection':False,
        'greater_budget_or_first_threshold_crossing_stop':False,
        'candidate_acceptance':'10*E accepted swaps within 200*E attempts AND removed_original_edges/E >=0.5',
        'ensemble_prediction':False,'uniform_sampling_or_independence_guarantee':False})
    proposal['epochs']['outer_refit_epochs']='floor(median(selected epochs on common valid inner folds)+0.5), separately per variant/null replicate; never outer-test early-stop'
    proposal['selection'].update({'common_inner_set':'intersection of topology-valid folds (all 3 nulls OK) and finite/evaluable validation folds for all 5 fits (noPPI, realPPI, 3 shuffled)',
        'minimum_valid_inner_folds':2,'skipped_inner_folds':'all variants excluded together from primary selection/epoch summary; frozen split membership unchanged',
        'fewer_valid_folds':'entire outer primary comparison NA_selection_insufficient, all three variants; no fit/fallback to rescue',
        'metric_NA_rule':'exclude only undefined/nonfinite or failed fit, never low metric; support/NA logged',
        'epoch_tie_rule':'earliest epoch; improvement requires > min_delta',
        'shuffle_summary':'metrics per fixed null replica plus equal mean of three metrics; no averaging PT predictions; no best replica'})
    proposal['null_failure_policy']={'inner':'Any failed null replica -> that inner fold excluded for ALL variants/replicas from primary comparison; raw failure NA retained',
        'outer':'Any failed final null replica -> entire outer primary triad comparison NA_null_outer; no replacement by real/noPPI',
        'minimum_common_inner':2,'numerical_or_metric_failure':'apply same common-fold rule after inner validation; no score-based fold selection',
        'cohort':'keep 62 IDs and reasons; report missing outer coverage, never call incomplete result full 5-fold/all62 performance',
        'old_failed_null':'old rep0 remains NA; rep1/rep2 never replace it'}
    proposal['open_gate']=['explicit training approval of v3 including missing-null/common-fold policy; no remaining automatic choices']
    if CONFIG.exists() and json.loads(CONFIG.read_text(encoding='utf-8'))!=proposal:raise RuntimeError('v3 proposal already frozen; use explicit new version')
    if not CONFIG.exists():write_json(CONFIG,proposal)
    write_json(QA/'policy_before_new_null_results.json',{'configuration_sha256':sha(CONFIG),
        'generator_sha256':sha(ROOT/'scripts/wp09_shuffle.py'),'diagnostic_horizons_swaps_per_edge':[10,50,100],
        'diagnostic_extra_swaps_not_used_for_production':True,'labels_or_performance_used':False})
    return proposal


def replay_trace(pairs,nodes,seed):
    """Eski RNG/işlem sırası aynen; 10E endpoint'i ve önceden yazılmış 50E/100E tanıları."""
    original=set(map(tuple,pairs));current=set(original);array=sorted(current);rng=np.random.default_rng(seed)
    m=len(array);attempts=accepted=0;reject=Counter();trace=[];ends=[]
    removed_total=reintroduced_total=0
    horizons={10*m,50*m,100*m}
    while accepted<100*m and attempts<2000*m:
        attempts+=1;i,j=rng.choice(m,2,replace=False)
        a,b=array[i];c,d=array[j]
        if rng.integers(2):a,b=b,a
        if rng.integers(2):c,d=d,c
        if len({a,b,c,d})!=4:reject['shared_endpoint']+=1;continue
        first=tuple(sorted((a,d)));second=tuple(sorted((c,b)))
        if first in current or second in current or first==second:reject['existing_or_duplicate_new_pair']+=1;continue
        old=(array[i],array[j]);removed_total+=sum(edge in original for edge in old)
        reintroduced_total+=sum(edge in original for edge in (first,second))
        current.remove(array[i]);current.remove(array[j]);current.update((first,second));array[i]=first;array[j]=second;accepted+=1
        changed=len(original-current)
        trace.append({'accepted_swaps':accepted,'attempts':attempts,'removed_original_edges':changed,
            'changed_fraction':changed/m,'original_edges_removed_cumulative':removed_total,
            'original_edges_reintroduced_cumulative':reintroduced_total})
        if accepted in horizons:
            ends.append({'accepted_swaps':accepted,'swaps_per_edge':accepted//m,'attempts':attempts,
                'shared_endpoint_rejections':reject['shared_endpoint'],
                'existing_pair_rejections':reject['existing_or_duplicate_new_pair'],
                'removed_original_edges':changed,'retained_original_edges':m-changed,'changed_fraction':changed/m,
                'edge_sha256':edge_hash(current),'passes_change_rule':changed/m>=.5,
                'original_edges_removed_cumulative':removed_total,'original_edges_reintroduced_cumulative':reintroduced_total})
    return pd.DataFrame(trace),pd.DataFrame(ends)


def common_scope(rows,metric_valid=None):
    """Yalnız status/missingness; metrik değerleri arayüze alınmaz."""
    for context,group in rows.groupby('context'):
        if set(group.replicate)!={0,1,2} or len(group)!=3:raise ValueError('All three fixed null replicas must be represented')
    context_valid=rows.groupby('context').status.apply(lambda s:s.eq('OK_degree_preserving_null').all()).to_dict()
    result=[]
    for (protocol,outer),sub in rows.groupby(['protocol','outer_fold']):
        inner=sub[sub.inner_fold.gt(0)][['context','inner_fold']].drop_duplicates().sort_values('inner_fold')
        valid=[r.inner_fold for r in inner.itertuples() if context_valid[r.context] and (metric_valid is None or metric_valid.get(r.context,False))]
        outer_context=sub[sub.inner_fold.eq(0)].context.unique()
        if len(outer_context)!=1:raise ValueError('One fixed outer-final context required')
        null_final=bool(context_valid[outer_context[0]])
        reason='READY_FOR_FUTURE_INNER_EVALUATION' if null_final and len(valid)>=2 else 'NA_null_outer' if not null_final else 'NA_insufficient_common_inner'
        result.append({'protocol':protocol,'outer_fold':int(outer),'common_valid_inner_folds':','.join(map(str,valid)),
            'common_valid_inner_count':len(valid),'outer_all_three_nulls_valid':null_final,
            'topology_preflight_status':reason,'training_authorized':False,
            'metric_evaluability_not_yet_tested':metric_valid is None})
    return pd.DataFrame(result)


def main():
    preserve();freeze_proposal()
    if (QA/'null_preflight_complete.json').exists():raise RuntimeError('Do not overwrite frozen v3 null preflight')
    old=pd.read_csv(DESIGN/'shuffle_quality.csv');old=old[old.threshold.eq(700)]
    failure=old[old.context.eq('stress_o02_i02')].iloc[0]
    with np.load(DESIGN/'folds/stress_o02_i02_train.npz',allow_pickle=False) as graph:
        pairs=list(map(tuple,graph['ppi_pairs_700'].T.tolist()));nodes=len(graph['protein_ids'])
    trace,endpoints=replay_trace(pairs,nodes,int(failure.seed))
    old_end=endpoints[endpoints.swaps_per_edge.eq(10)].iloc[0]
    assert old_end.edge_sha256==failure.shuffled_edge_sha256 and old_end.attempts==failure.attempts
    degree=np.bincount(np.asarray(pairs).ravel(),minlength=nodes);active=degree[degree>0]
    write_csv('failure_full_swap_trace.csv',trace);write_csv('failure_fixed_horizon_diagnostics.csv',endpoints)
    write_csv('failure_node_degrees.csv',pd.DataFrame({'node_index':np.arange(nodes),'degree':degree}))
    write_json(QA/'failure_diagnosis.json',{'context':str(failure.context),'seed':int(failure.seed),'nodes_all':nodes,
        'active_degree_nodes':int(len(active)),'edges':len(pairs),'minimum_removed_for_50pct':math.ceil(.5*len(pairs)),
        'old_removed_original_edges':int(old_end.removed_original_edges),'old_retained_original_edges':int(old_end.retained_original_edges),
        'accepted_swap_target_met':True,'attempt_budget_exhausted':bool(failure.attempts>=failure.attempt_budget),
        'budget':int(failure.attempt_budget),'old_attempts':int(failure.attempts),'maximum_degree':int(active.max()),
        'first_10E_max_removed_edges':int(trace[trace.accepted_swaps.le(10*len(pairs))].removed_original_edges.max()),
        'first_10E_crossed_50pct_before_final':bool((trace[trace.accepted_swaps.le(10*len(pairs))].changed_fraction>=.5).any()),
        'old_endpoint_hash_reproduced':True,'extended_endpoint_not_used_as_replacement':True,
        'mixing_or_impossibility_claim':False})
    folder=QA/'nulls';folder.mkdir(exist_ok=True);rows=[]
    contexts=sorted(old.context.unique())
    for context in contexts:
        record=old[old.context.eq(context)].iloc[0]
        with np.load(DESIGN/'folds'/(context+'_train.npz'),allow_pickle=False) as archive:
            pairs=list(map(tuple,archive['ppi_pairs_700'].T.tolist()));nodes=len(archive['protein_ids'])
        for replicate in range(3):
            seed=int(record.seed)+1000000*replicate
            null,info=shuffle_pairs(pairs,nodes,seed)
            if replicate==0:
                assert info['shuffled_edge_sha256']==record.shuffled_edge_sha256 and info['status']==record.status
            row={'context':context,'protocol':record.protocol,'outer_fold':int(record.outer_fold),
                'inner_fold':int(record.inner_fold),'threshold':700,'replicate':replicate,**info}
            if info['status']=='OK_degree_preserving_null':
                path=folder/f'{context}_r{replicate}.npz'
                np.savez_compressed(path,ppi_pairs=np.asarray(null,dtype=np.int64).reshape(-1,2).T)
                row['artifact_file']=path.relative_to(ROOT).as_posix();row['artifact_sha256']=sha(path)
            else:row.update(artifact_file='',artifact_sha256='')
            rows.append(row)
    result=pd.DataFrame(rows);write_csv('null_preflight_700_three_replicates.csv',result)
    write_csv('common_inner_outer_preflight.csv',common_scope(result))
    inputs=[DESIGN/'shuffle_quality.csv',ROOT/'scripts/wp09_shuffle.py',ROOT/'configs/WP09_training_PROPOSED_v2.json']
    inputs+=list((DESIGN/'folds').glob('*_train.npz'))
    write_json(QA/'input_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in inputs})
    write_json(QA/'null_preflight_complete.json',{'threshold':700,'replicates':3,'contexts':40,'candidates':len(rows),
        'accepted':int(result.status.eq('OK_degree_preserving_null').sum()),'NA':int(result.status.ne('OK_degree_preserving_null').sum()),
        'old_replicate_zero_40_exactly_reproduced':True,'training_or_optimizer_or_PT_scores':False,
        'config_sha256':sha(CONFIG),'prior_files_verified':preserve()})
    print(json.dumps(json.loads((QA/'failure_diagnosis.json').read_text(encoding='utf-8')),ensure_ascii=False),flush=True)
    print(common_scope(result).to_string(index=False),flush=True)


def training_preview():
    """Yalnız denetlenebilir iş listesi; eğitim döngüsü veya skor fonksiyonu değildir."""
    preserve()
    preflight=pd.read_csv(QA/'common_inner_outer_preflight.csv',keep_default_na=False)
    prep=ROOT/'reports/qa/WP08/experimental_preparation'
    parts=pd.read_csv(prep/'nested_partitions_v1.csv')
    eligible=pd.read_csv(prep/'prediction_eligibility.csv')
    eligible=set(eligible[eligible.model.eq('B2')&eligible.eligible].drug_id)
    vocab=json.loads((prep/'train_vocabularies.json').read_text(encoding='utf-8'))
    fittable=json.loads((prep/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
    rows=[];source={}
    def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for row in preflight.itertuples():
        inners=[int(x) for x in str(row.common_valid_inner_folds).split(',') if x]
        if row.topology_preflight_status!='READY_FOR_FUTURE_INNER_EVALUATION':continue
        for inner in inners+[0]:
            context=f'{row.protocol}_o{row.outer_fold:02}_'+(f'i{inner:02}' if inner else 'final')
            local=parts[parts.context.eq(context)]
            ids={split:sorted(local[local.split.eq(split)].drug_id) for split in ('train','validation','test')}
            source[context]={'graph_train_ids':ids['train'],'fit_eligible_train_ids':sorted(set(ids['train'])&eligible),
                'validation_query_ids':ids['validation'],'test_query_ids':ids['test'],
                'declared_train_B2_PT':vocab[context]['B2'],'fittable_train_B2_PT':fittable[context]['B2']}
            assert set(source[context]['fittable_train_B2_PT'])<=set(source[context]['declared_train_B2_PT'])
            for variant,replicate in [('G_noPPI',-1),('G_realPPI',-1)]+[('G_shuffledPPI',r) for r in range(3)]:
                null_file='' if replicate<0 else f'reports/qa/WP09/null_gate_v3/nulls/{context}_r{replicate}.npz'
                if null_file and not (ROOT/null_file).exists():raise AssertionError('Preview cannot schedule missing null')
                rows.append({'context':context,'protocol':row.protocol,'outer_fold':row.outer_fold,'inner_fold':inner,
                    'phase':'INNER_EARLY_STOP' if inner else 'OUTER_FINAL_CONDITIONAL_ON_INNER',
                    'variant':variant,'null_replicate':replicate,'null_file':null_file,
                    'init_seed':20261106+(0 if row.protocol=='primary' else 10000)+100*row.outer_fold+inner,
                    'train_fit_count':len(source[context]['fit_eligible_train_ids']),
                    'identity_and_target_scope_sha256':digest(source[context]),
                    'training_graph_file':f'reports/qa/WP09/design_v1/folds/{context}_train.npz',
                    'query_file':f'reports/qa/WP09/design_v1/folds/{context}_query.npz',
                    'status':'NOT_RUN_AWAITING_USER_APPROVAL'})
    write_json(QA/'training_preview_sources.json',source)
    write_csv('training_sequence_PREVIEW_ONLY.csv',pd.DataFrame(rows))
    inputs=[prep/x for x in ('nested_partitions_v1.csv','prediction_eligibility.csv','train_vocabularies.json','train_fittable_vocabularies_NO_model_fit.json')]
    write_json(QA/'schedule_input_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in inputs})
    print(f'Preview only: {len(rows)} conditional future fit jobs; no job executed')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['snapshot','preflight','preserve','plan'])
    action=parser.parse_args().action
    if action=='snapshot':snapshot()
    elif action=='preflight':main()
    elif action=='plan':training_preview()
    else:print(preserve())
