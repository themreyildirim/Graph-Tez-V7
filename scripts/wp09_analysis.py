"""Gerçek fold topolojisi, ilaç kapsamı ve eğitimsiz encoder kanıtı."""
import copy
import json
import time
import numpy as np
import pandas as pd
import networkx as nx
import torch
from wp09_data import ROOT,QA,PREP,ROLES,THRESHOLDS,load_sources,edge_array,csv_write,json_write,preserve,sha
from wp09_encoder import RoleMaskedPPI,directed_edges,distinguishing_fixture
from wp09_shuffle import shuffle_pairs,SHUFFLE_POLICY


def proposed_config():
    return {'version':'WP09-training-PROPOSED-v1','status':'AWAITING_SEPARATE_TRAINING_APPROVAL','training_enabled':False,
        'scope_now':'design/data/forward-gradient validation only','exploratory_after_seen_WP08_baselines':True,
        'cohort':62,'proxy':'observed SIDER record; unknown NOT verified negative; not clinical risk',
        'threshold':{'recommended_primary':400,'approved_primary':None,'sensitivities':[700,900],
            'reason':'label-independent coverage-first topology; not performance optimality'},
        'architecture':{'protein_features':56,'protein_hidden':32,'PPI_layers':1,'chemistry_hidden':8,
            'role_readout':'four separate masked means','drug_representation_dim':141,
            'head':'single linear train-PT logits','batchnorm':False,'dropout':0.,
            'message':'z=relu(Px); h=z+relu(Sz+M mean_neighbor(z)); empty neighbors mean zero'},
        'optimizer':{'name':'AdamW','learning_rate':.001,'weight_decay':.001},
        'loss':{'name':'BCEWithLogitsLoss','reduction':'mean over valid train targets per eligible drug, then mean drugs',
            'unknown_encoding':'0 proxy only, not verified negative','class_weight':None,'pos_weight':None,
            'single_proxy_outcome_train_target':'NA; no fallback'},
        'epochs':{'maximum':200,'inner_early_stopping':'drug-macro observed-record AP','patience':20,'min_delta':.0001,
            'restore':'best inner validation epoch; ties earliest',
            'outer_refit_epochs':'rounded median of valid selected inner epochs; no outer test early stopping'},
        'selection':{'new_hyperparameter_search':False,'minimum_valid_inner_folds':2,
            'fewer_valid_folds':'outer result NA_selection_insufficient; no constant fallback',
            'candidate_target_scope':'frozen B2 train dictionary and shared train-fittable mask; same within each inner fold',
            'outer_test_for_decisions':False,'fixed_references':'WP08 B0/B1/B2 no refit'},
        'seed':{'base':20261106,'init_formula':'base + 10000*protocol_index + 100*outer_fold + inner_fold',
            'same_initial_state_across_ablations':True,'seed_search':False,'device':'CPU','threads':1,
            'deterministic_algorithms':True,'cross_version_bitwise_guarantee':False},
        'PPI_universe':'only train-linked validated sequence accessions; strict human induced PPI',
        'query':'unseen sequence accession self-only; no query-to-train messages; missing all modalities abstain',
        'context80':False,'K12_MG1655_PPI_in_human':False,'STRING_score_as_feature_or_weight':False,
        'shuffle':SHUFFLE_POLICY,
        'future_null_replicate_seeds':'design_seed + 1000000*replicate_index, indices 0,1,2; no cherry-picking',
        'evaluation':'not executed; same frozen primary/stress split; exact paired54/NA scope, own61 separate',
        'uncertainty':'future fixed OOF structural-group paired bootstrap, conditional; not external validation',
        'open_gate':['primary PPI threshold','projection/readout capacity','proxy loss and optimizer/LR',
            'epoch/early-stop/outer refit policy','seed policy','shuffle attempts/change threshold/three null replicates']}


def synthetic_proof():
    encoder,x,pairs=distinguishing_fixture()
    before=encoder(x,directed_edges(pairs))
    removed=np.array([[0,1]],dtype=np.int64).T
    after=encoder(x,directed_edges(removed))
    changed_x=x.clone();changed_x[2,0]+=2
    neighbor_changed=encoder(changed_x,directed_edges(pairs))
    rows=[]
    for i,name in enumerate('ABCD'):
        rows.append({'protein':name,'x0':float(x[i,0]),'x1':float(x[i,1]),
            'before_h0':float(before[i,0].detach()),'before_h1':float(before[i,1].detach()),
            'BC_removed_h0':float(after[i,0].detach()),'BC_removed_h1':float(after[i,1].detach()),
            'C_x0_plus2_h0':float(neighbor_changed[i,0].detach()),
            'edge_removal_changes_representation':bool(not torch.equal(before[i],after[i]))})
    csv_write(QA/'synthetic_forward_proof.csv',pd.DataFrame(rows))
    gradient_x=x.clone().requires_grad_(True)
    result=encoder(gradient_x,directed_edges(pairs));result[1,0].backward()
    gradients=[{'output':'B_h0','input_protein':name,'derivative_wrt_x0':float(gradient_x.grad[i,0]),
        'interpretation':'one-hop neighbor' if i in (0,2) else 'self residual' if i==1 else 'outside receptive field'} for i,name in enumerate('ABCD')]
    csv_write(QA/'synthetic_gradient_proof.csv',pd.DataFrame(gradients))
    json_write(QA/'synthetic_message_trace.json',{'message_weight_gradient_norm':float(encoder.message.weight.grad.norm()),
        'expected_C_x0_to_B_h0_gradient':.5,'observed':float(gradient_x.grad[2,0]),
        'edge_removal_expected_changed':['B','C'],'unchanged':['A','D'],
        'loss_or_optimizer_update':False,'clinical_prediction':False})


def main():
    preserve();started=time.perf_counter();data=load_sources()
    if (QA/'analysis_complete.json').exists():raise RuntimeError('Analysis design-v1 already completed; do not redefine policy from results')
    config=proposed_config();config_path=ROOT/'configs/WP09_training_PROPOSED_v1.json'
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8'))!=config:raise RuntimeError('Proposed v1 policy changed')
    json_write(config_path,config);json_write(QA/'shuffle_policy_before_analysis.json',SHUFFLE_POLICY)
    topo=[];drug_rows=[];protein_rows=[];nulls=[];encoder_rows=[]
    shuffle_dir=QA/'shuffled';shuffle_dir.mkdir(exist_ok=True)
    strict_accessions=set(data['strict'].accession)
    torch.set_num_threads(1);torch.manual_seed(20261106)
    encoder=RoleMaskedPPI().double().eval()
    for context_index,context in enumerate(sorted(data['partitions'].context.unique())):
        sub=data['partitions'][data['partitions'].context.eq(context)];meta=sub.iloc[0]
        with np.load(QA/'folds'/(context+'_train.npz'),allow_pickle=False) as archive:graph={k:archive[k] for k in archive.files}
        with np.load(QA/'folds'/(context+'_query.npz'),allow_pickle=False) as archive:query={k:archive[k] for k in archive.files}
        proteins=list(graph['protein_ids']);n=len(proteins);human={i for i,p in enumerate(proteins) if p in strict_accessions}
        split_map=dict(zip(sub.drug_id,sub.split));null_bundle={}
        for threshold in THRESHOLDS:
            pairs=[tuple(e) for e in graph[f'ppi_pairs_{threshold}'].T.tolist()]
            network=nx.Graph();network.add_nodes_from(human);network.add_edges_from(pairs)
            degree=dict(network.degree());incident={i for i,d in degree.items() if d>0}
            common={'context':context,'protocol':meta.protocol,'outer_fold':int(meta.outer_fold),'inner_fold':int(meta.inner_fold),'threshold':threshold}
            topo.append({**common,'train_drugs':len(graph['drug_ids']),'all_sequence_proteins':n,'strict_human_nodes':len(human),
                'human_PPI_message_nodes':len(incident),'human_isolates':len(human)-len(incident),
                'all_sequence_no_PPI_nodes':n-len(incident),'undirected_pairs':len(pairs),'directed_columns':2*len(pairs),
                'human_components':nx.number_connected_components(network),
                'human_largest_component':max(map(len,nx.connected_components(network)),default=0),
                'human_density':nx.density(network),'clinical_or_performance_measure':False})
            for i,accession in enumerate(proteins):protein_rows.append({**common,'accession':accession,
                'strict_human':i in human,'PPI_degree':degree.get(i,0),'can_receive_PPI_message':i in incident,
                'sequence_self_path_retained':True})
            message_accessions={proteins[i] for i in incident}
            for drug in sorted(sub.drug_id):
                related=data['relations'][data['relations'].drug_id.eq(drug)]
                for role in ('ALL',)+ROLES:
                    acc=set(related.accession if role=='ALL' else related[related.role.eq(role)].accession)
                    seen=acc&set(proteins);unseen=acc-set(proteins)
                    drug_rows.append({**common,'drug_id':drug,'split':split_map[drug],'role':role,
                        'linked_sequence_proteins':len(acc),'strict_human_linked':len(acc&strict_accessions),
                        'in_train_protein_universe':len(seen),'query_unseen_self_only':len(unseen),
                        'PPI_message_proteins':len(acc&message_accessions),'has_any_PPI_message':bool(acc&message_accessions),
                        'PPI_message_fraction':len(acc&message_accessions)/len(acc) if acc else None,
                        'no_protein_modality':not bool(acc)})
            seed=20261106+10000+100*context_index+threshold
            shuffled,info=shuffle_pairs(pairs,n,seed,SHUFFLE_POLICY['swaps_per_edge'],SHUFFLE_POLICY['attempts_per_edge'],SHUFFLE_POLICY['minimum_changed_fraction'])
            nulls.append({**common,**info})
            # Başarısız null boş/gerçek kenar ile ikame edilmez; durum ayrı saklanır.
            if info['status']=='OK_degree_preserving_null':null_bundle[f'ppi_pairs_{threshold}']=edge_array(shuffled)
            with torch.no_grad():
                representation=encoder.forward(graph,threshold,'G_realPPI')
                cached=representation['protein_h'].clone()
                query_out=encoder.query_readout(query,cached)
                encoder_rows.append({**common,'train_protein_rows':len(cached),'hidden':cached.shape[1],
                    'finite_train_representations':bool(torch.isfinite(cached).all()),
                    'finite_query_representations':bool(torch.isfinite(query_out['representation']).all()),
                    'cache_unchanged_after_query':bool(torch.equal(cached,representation['protein_h'])),
                    'num_train_eligible':int(representation['eligible'].sum()),'num_query_eligible':int(query_out['eligible'].sum()),
                    'PT_head_present':encoder.head is not None,'optimizer_steps':0,'performance_computed':False})
        np.savez_compressed(shuffle_dir/(context+'.npz'),**null_bundle)
    for name,rows in [('fold_ppi_topology.csv',topo),('drug_ppi_coverage.csv',drug_rows),
        ('protein_message_scope.csv',protein_rows),('shuffle_quality.csv',nulls),('real_encoder_shape_checks.csv',encoder_rows)]:
        csv_write(QA/name,pd.DataFrame(rows))
    coverage=pd.DataFrame(drug_rows)
    summary=coverage.groupby(['context','protocol','outer_fold','inner_fold','threshold','split','role']).agg(
        drugs=('drug_id','nunique'),drugs_with_PPI=('has_any_PPI_message','sum'),
        linked_proteins_sum=('linked_sequence_proteins','sum'),message_proteins_sum=('PPI_message_proteins','sum'),
        query_unseen_proteins_sum=('query_unseen_self_only','sum')).reset_index()
    csv_write(QA/'fold_drug_coverage_summary.csv',summary)
    synthetic_proof()
    json_write(QA/'shuffled_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in shuffle_dir.glob('*.npz')})
    json_write(QA/'analysis_complete.json',{'contexts':40,'threshold_scenarios':120,'training_performed':False,
        'optimizer_steps':0,'PT_head_on_real_data':False,'performance_comparison':False,'selected_threshold':None,
        'proposed_threshold':400,'threshold_proposal_basis':'label-independent coverage/topology; awaiting user approval',
        'prior_files_verified':preserve(),'elapsed_seconds':time.perf_counter()-started,
        'shuffle_successes':sum(r['status']=='OK_degree_preserving_null' for r in nulls),'shuffle_total':len(nulls),
        'config_sha256':sha(config_path)})
    print('WP09 topology/coverage + 120 degree-preserving null checks + untrained encoder mechanics complete; no performance')


if __name__=='__main__':main()
