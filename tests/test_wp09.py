"""WP09 tasarım: gerçek fold sınırları, forward/gradient ve null doğrulaması; eğitim yok."""
from pathlib import Path
import sys,copy,json,hashlib,unittest,ast
import numpy as np
import pandas as pd
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp09_data import QA,PREP,ROLES,THRESHOLDS,load_sources,build_context,validate_bundle,preserve
from wp09_encoder import RoleMaskedPPI,distinguishing_fixture,directed_edges
from wp09_shuffle import shuffle_pairs


def bundle(context,kind):
    with np.load(QA/'folds'/(context+'_'+kind+'.npz'),allow_pickle=False) as source:return {k:source[k] for k in source.files}


class WP09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        torch.manual_seed(20261106)
        cls.data=load_sources();cls.context='primary_o01_final'
        cls.graph=bundle(cls.context,'train');cls.query=bundle(cls.context,'query')
        cls.quality=pd.read_csv(QA/'shuffle_quality.csv')

    def test_01_all_prior_outputs_unchanged(self):
        self.assertGreaterEqual(preserve(),1392)

    def test_02_inputs_and_prepared_hashes_unchanged(self):
        for name in ('input_manifest.json','prepared_artifact_manifest.json','shuffled_artifact_manifest.json'):
            paths=json.loads((QA/name).read_text(encoding='utf-8'))
            self.assertEqual([],[p for p,h in paths.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])

    def test_03_all_40_frozen_partitions_train_only_and_query_separate(self):
        for context,sub in self.data['partitions'].groupby('context'):
            graph=bundle(context,'train');query=bundle(context,'query')
            self.assertTrue(validate_bundle(graph,query))
            self.assertEqual(set(graph['drug_ids']),set(sub[sub.split.eq('train')].drug_id))
            self.assertEqual(set(query['drug_ids']),set(sub[sub.split.ne('train')].drug_id))
            self.assertEqual(len(graph['drug_ids'])+len(query['drug_ids']),62)

    def test_04_transforms_exact_frozen_train_sources(self):
        for context in self.data['partitions'].context.unique():
            graph=bundle(context,'train');s=self.data['stats'][context]
            self.assertEqual(list(graph['protein_ids']),s['protein_fit_accessions'])
            raw=self.data['protein'].set_index('accession').loc[graph['protein_ids'],self.data['protein_columns']]
            expected=(raw-pd.Series(s['protein']['mean']))/pd.Series(s['protein']['scale'])
            np.testing.assert_allclose(graph['protein_x'],expected.to_numpy(),rtol=0,atol=1e-12)

    def test_05_real_pairs_match_source_all_thresholds(self):
        strict=self.data['strict'];sid=dict(zip(strict.string_id,strict.accession))
        for context in self.data['partitions'].context.unique():
            graph=bundle(context,'train');index={a:i for i,a in enumerate(graph['protein_ids'])}
            for threshold in THRESHOLDS:
                expected=set()
                for row in self.data['ppi'].itertuples():
                    a,b=sid[row.protein1],sid[row.protein2]
                    if not row.score_conflict and row.combined_score>=threshold and a in index and b in index:
                        expected.add(tuple(sorted((index[a],index[b]))))
                self.assertEqual(set(map(tuple,graph[f'ppi_pairs_{threshold}'].T)),expected)

    def test_06_nonPPI_and_nonhuman_sequences_retained(self):
        graph=self.graph;train=set(graph['drug_ids'])
        expected=set(self.data['relations'][self.data['relations'].drug_id.isin(train)].accession)
        self.assertEqual(set(graph['protein_ids']),expected)
        incident=set(graph['ppi_pairs_900'].ravel());self.assertLess(len(incident),len(expected))
        model=RoleMaskedPPI().double().eval()
        h=model.forward(graph,900,'G_realPPI')['protein_h']
        self.assertEqual(len(h),len(expected));self.assertTrue(torch.isfinite(h).all())

    def test_07_B2_eligibility_62_and_QC_unchanged(self):
        eligible=self.data['eligibility'].query("model == 'B2'").set_index('drug_id').eligible
        self.assertEqual(int(eligible.sum()),61);self.assertFalse(eligible['DB06799'])
        self.assertTrue(eligible['DB00684'])
        for block in (self.graph,self.query):np.testing.assert_array_equal(block['eligible'],eligible.loc[block['drug_ids']])

    def test_08_four_typed_role_edges_exact(self):
        graph=self.graph;relations=self.data['relations']
        for role in ROLES:
            expected={(r.drug_id,r.accession) for r in relations[relations.drug_id.isin(graph['drug_ids'])&relations.role.eq(role)].itertuples()}
            actual={(graph['drug_ids'][a],graph['protein_ids'][b]) for a,b in graph['role_'+role].T}
            self.assertEqual(actual,expected)

    def test_09_heldout_relations_cannot_change_train_graph(self):
        altered=dict(self.data);train=set(self.graph['drug_ids'])
        altered['relations']=self.data['relations'][self.data['relations'].drug_id.isin(train)].copy()
        graph,_=build_context(altered,self.context,include_query=False)
        for name in graph:np.testing.assert_array_equal(graph[name],self.graph[name])

    def test_10_heldout_chemistry_values_do_not_change_train(self):
        altered=dict(self.data);altered['chem']=self.data['chem'].copy()
        altered['chem'].loc[~altered['chem'].id.isin(self.graph['drug_ids']),['MW','LogP','HBD','HBA','TPSA']]=1e12
        graph,_=build_context(altered,self.context)
        for name in graph:np.testing.assert_array_equal(graph[name],self.graph[name])

    def test_11_target_or_reverse_edge_injection_rejected(self):
        for name in ('y','pt_cui','side_effect_edges','reverse_target_edges','kalite_skoru'):
            changed=dict(self.graph);changed[name]=np.zeros((1,))
            with self.assertRaises(ValueError):validate_bundle(changed)

    def test_12_K12_edge_and_context_accession_rejected(self):
        from wp09_data import ppi_pairs
        changed=dict(self.data);changed['ppi']=self.data['ppi'].copy()
        changed['ppi'].loc[0,'network_taxid']=511145
        with self.assertRaises(ValueError):ppi_pairs(changed,list(self.graph['protein_ids']),400)
        changed=dict(self.data);changed['relations']=self.data['relations'].copy()
        changed['relations'].loc[0,'accession']='CONTEXT_WITHOUT_SEQUENCE'
        with self.assertRaises(ValueError):build_context(changed,self.context)

    def test_13_analytical_edge_removal_changes_only_B_C(self):
        model,x,pairs=distinguishing_fixture();before=model(x,directed_edges(pairs))
        after=model(x,directed_edges(np.array([[0,1]],dtype=np.int64).T))
        np.testing.assert_allclose(before.detach(),[[5,5],[7.5,5],[7,9],[10,10]])
        np.testing.assert_allclose(after.detach(),[[5,5],[7,4],[4,8],[10,10]])
        self.assertEqual((before!=after).any(dim=1).tolist(),[False,True,True,False])

    def test_14_one_hop_neighbor_perturbation_locality(self):
        model,x,pairs=distinguishing_fixture();before=model(x,directed_edges(pairs));changed=x.clone();changed[2,0]+=2
        difference=model(changed,directed_edges(pairs))-before
        np.testing.assert_allclose(difference.detach(),[[0,0],[1,0],[4,0],[0,0]])

    def test_15_neighbor_and_message_gradient_nonzero(self):
        model,x,pairs=distinguishing_fixture();x.requires_grad_(True)
        model(x,directed_edges(pairs))[1,0].backward()
        np.testing.assert_allclose(x.grad[:,0],[.5,2,.5,0])
        self.assertGreater(float(model.message.weight.grad.norm()),0)

    def test_16_message_trace_has_real_neighbor_means(self):
        model,x,pairs=distinguishing_fixture();captured=[]
        handle=model.message.register_forward_pre_hook(lambda module,args:captured.append(args[0].detach().clone()))
        model(x,directed_edges(pairs));handle.remove()
        np.testing.assert_allclose(captured[0],[[3,1],[1.5,3],[3,1],[0,0]])

    def test_17_noPPI_is_actual_empty_message_path(self):
        model=RoleMaskedPPI().double().eval();x=torch.tensor(self.graph['protein_x'])
        a=model.encode_proteins(x,self.graph['ppi_pairs_400'],'G_noPPI')
        b=model.encode_proteins(x,np.empty((2,0),dtype=np.int64),'G_realPPI')
        torch.testing.assert_close(a,b,rtol=0,atol=0)

    def test_18_shuffled_variant_cannot_silently_use_real_edges(self):
        model=RoleMaskedPPI().double().eval()
        with self.assertRaises(ValueError):model.forward(self.graph,700,'G_shuffledPPI')
        with np.load(QA/'shuffled'/(self.context+'.npz'),allow_pickle=False) as null:
            output=model.forward(self.graph,700,'G_shuffledPPI',null['ppi_pairs_700'])
        self.assertIsNone(output['logits']);self.assertTrue(torch.isfinite(output['protein_h']).all())

    def test_19_node_permutation_equivariance(self):
        model,x,pairs=distinguishing_fixture();permutation=np.array([2,0,3,1]);inverse=np.argsort(permutation)
        permuted_pairs=np.sort(inverse[pairs],axis=0)
        a=model(x,directed_edges(pairs));b=model(x[permutation],directed_edges(permuted_pairs))
        torch.testing.assert_close(a[permutation],b)

    def test_20_role_means_remain_separate(self):
        model=RoleMaskedPPI(hidden=2,chem_hidden=1).double()
        h=torch.tensor([[2.,4.],[6.,8.]],dtype=torch.float64)
        roles={r:torch.empty((2,0),dtype=torch.long) for r in ROLES}
        roles['target']=torch.tensor([[0,0],[0,1]]);roles['enzyme']=torch.tensor([[0],[0]])
        out=model.readout(h,torch.zeros((1,5),dtype=torch.float64),torch.tensor([[False,True,True,False,False]]),roles)
        torch.testing.assert_close(out['representation'][0,1:5],torch.tensor([4.,6.,2.,4.],dtype=torch.float64))

    def test_21_query_cannot_mutate_train_embedding_or_state(self):
        model=RoleMaskedPPI().double().eval();out=model.forward(self.graph,700,'G_realPPI')
        cache=out['protein_h'].detach().clone();before=cache.clone();state=copy.deepcopy(model.state_dict())
        model.query_readout(self.query,cache)
        changed={k:v.copy() for k,v in self.query.items()};changed['chemistry'][changed['masks'][:,0]]+=123
        model.query_readout(changed,cache)
        torch.testing.assert_close(cache,before,rtol=0,atol=0)
        for name,value in state.items():torch.testing.assert_close(model.state_dict()[name],value,rtol=0,atol=0)
        self.assertFalse(any(isinstance(m,torch.nn.modules.batchnorm._BatchNorm) for m in model.modules()))

    def test_22_unseen_query_protein_self_only(self):
        model=RoleMaskedPPI(hidden=2,chem_hidden=1).double().eval()
        query={'unseen_protein_x':np.ones((1,56)),'chemistry':np.zeros((1,5)),
            'masks':np.array([[False,True,False,False,False]],dtype=bool),
            **{'role_'+r:np.empty((2,0),dtype=np.int64) for r in ROLES}}
        query['role_target']=np.array([[0],[0]],dtype=np.int64)
        out=model.query_readout(query,torch.empty((0,2),dtype=torch.float64))
        expected=model.protein(torch.ones((1,56),dtype=torch.float64),torch.empty((2,0),dtype=torch.long))
        torch.testing.assert_close(out['representation'][:,1:3],expected)

    def test_23_all_input_missing_abstention_and_masked_bias(self):
        model=RoleMaskedPPI(hidden=2,chem_hidden=1,num_targets=3).double()
        roles={r:torch.empty((2,0),dtype=torch.long) for r in ROLES}
        out=model.readout(torch.empty((0,2),dtype=torch.float64),torch.zeros((1,5),dtype=torch.float64),torch.zeros((1,5),dtype=torch.bool),roles)
        self.assertFalse(out['eligible'][0]);self.assertTrue(torch.isnan(out['logits']).all())
        self.assertTrue((out['representation']==0).all())

    def test_24_actual_null_degrees_edge_counts_and_status(self):
        for row in self.quality.itertuples():
            graph=bundle(row.context,'train');original=graph[f'ppi_pairs_{row.threshold}']
            with np.load(QA/'shuffled'/(row.context+'.npz'),allow_pickle=False) as source:
                key=f'ppi_pairs_{row.threshold}'
                if row.status!='OK_degree_preserving_null':
                    self.assertNotIn(key,source.files);continue
                shuffled=source[key]
            self.assertEqual(shuffled.shape,original.shape)
            np.testing.assert_array_equal(np.bincount(original.ravel(),minlength=len(graph['protein_ids'])),
                np.bincount(shuffled.ravel(),minlength=len(graph['protein_ids'])))
            self.assertTrue((shuffled[0]<shuffled[1]).all());self.assertEqual(len(set(map(tuple,shuffled.T))),shuffled.shape[1])
            changed=len(set(map(tuple,original.T))-set(map(tuple,shuffled.T)))/original.shape[1]
            self.assertAlmostEqual(changed,row.changed_fraction);self.assertGreaterEqual(changed,.5)

    def test_25_shuffle_reproducibility_and_degree_preservation(self):
        pairs=[(0,1),(1,2),(2,3),(3,4),(4,5),(0,5)]
        a,info=shuffle_pairs(pairs,6,20261106);b,other=shuffle_pairs(pairs,6,20261106)
        self.assertEqual(a,b);self.assertEqual(info,other)
        np.testing.assert_array_equal(np.bincount(np.asarray(pairs).ravel()),np.bincount(np.asarray(a).ravel()))

    def test_26_infeasible_shuffle_is_NA_not_success(self):
        clique=[(a,b) for a in range(5) for b in range(a+1,5)]
        edges,info=shuffle_pairs(clique,5,9)
        self.assertEqual(info['status'],'NA_shuffle_insufficient');self.assertEqual(info['changed_fraction'],0.)
        self.assertEqual(edges,clique)
        for bad in ([(0,0)],[(0,1),(0,1)],[(0,9)]):
            with self.assertRaises(ValueError):shuffle_pairs(bad,5,1)

    def test_27_null_edges_never_use_nonhuman_or_context(self):
        human=set(self.data['strict'].accession)
        for context in self.data['partitions'].context.unique():
            graph=bundle(context,'train')
            with np.load(QA/'shuffled'/(context+'.npz'),allow_pickle=False) as archive:
                for key in archive.files:self.assertTrue(set(graph['protein_ids'][archive[key].ravel()])<=human)

    def test_28_drug_message_coverage_independent_first_context(self):
        rows=pd.read_csv(QA/'drug_ppi_coverage.csv');rows=rows[rows.context.eq(self.context)&rows.role.eq('ALL')]
        for threshold in THRESHOLDS:
            incident=set(self.graph['protein_ids'][self.graph[f'ppi_pairs_{threshold}'].ravel()])
            for row in rows[rows.threshold.eq(threshold)].itertuples():
                related=set(self.data['relations'][self.data['relations'].drug_id.eq(row.drug_id)].accession)
                self.assertEqual(row.PPI_message_proteins,len(incident&related))

    def test_29_topology_matches_unchanged_WP08_preflight(self):
        actual=pd.read_csv(QA/'fold_ppi_topology.csv')
        old=pd.read_csv(ROOT/'reports/qa/WP08/final_closure_v1/WP09_train_only_topology_preflight.csv')
        matched=actual.merge(old,on=['context','threshold'],validate='one_to_one')
        np.testing.assert_array_equal(matched.undirected_pairs,matched.undirected_PPI_pairs)
        np.testing.assert_array_equal(matched.human_isolates,matched.isolated_human_nodes)

    def test_30_bad_indices_duplicates_and_mask_contradictions_rejected(self):
        for bad in (np.array([[0],[0]]),np.array([[0,0],[1,1]]),np.array([[0.],[1.]])):
            with self.assertRaises(ValueError):directed_edges(bad)
        changed={k:v.copy() for k,v in self.graph.items()};changed['role_target'][0,0]=99999
        with self.assertRaises(ValueError):validate_bundle(changed)
        changed={k:v.copy() for k,v in self.graph.items()};changed['masks'][:,1]=False
        with self.assertRaises(ValueError):validate_bundle(changed)

    def test_31_no_training_steps_or_actual_PT_head(self):
        checks=pd.read_csv(QA/'real_encoder_shape_checks.csv')
        self.assertEqual(len(checks),120);self.assertTrue(checks.optimizer_steps.eq(0).all())
        self.assertFalse(checks.PT_head_present.any() or checks.performance_computed.any())
        self.assertTrue(checks.cache_unchanged_after_query.all())
        for name in ('wp09_encoder.py','wp09_analysis.py'):
            tree=ast.parse((ROOT/'scripts'/name).read_text(encoding='utf-8'))
            calls=[node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
            self.assertNotIn('step',calls);self.assertNotIn('zero_grad',calls)

    def test_32_proposed_config_gate_closed_and_all_scenarios_retained(self):
        config=json.loads((ROOT/'configs/WP09_training_PROPOSED_v1.json').read_text(encoding='utf-8'))
        self.assertFalse(config['training_enabled']);self.assertIsNone(config['threshold']['approved_primary'])
        self.assertEqual(config['seed']['base'],20261106)
        self.assertEqual(config['architecture']['protein_features'],56)
        topology=pd.read_csv(QA/'fold_ppi_topology.csv')
        self.assertEqual(len(topology),120);self.assertEqual(set(topology.threshold),{400,700,900})

    def test_33_null_failure_not_claimed_mathematical_impossibility(self):
        limits=pd.read_csv(QA/'shuffle_structural_limits.csv')
        self.assertEqual(len(limits),120)
        self.assertTrue((limits.changed_fraction<=limits.necessary_upper_bound_on_changed_fraction+1e-12).all())
        self.assertTrue(limits.bound_is_not_constructive_maximum.all())
        self.assertFalse(limits.raw_50pct_change_mathematically_excluded_by_bound.any())

    def test_34_revised_recommendation_is_explicit_unapproved_and_label_blind(self):
        v1=ROOT/'configs/WP09_training_PROPOSED_v1.json'
        v2=json.loads((ROOT/'configs/WP09_training_PROPOSED_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(v2['previous_proposal_sha256'],hashlib.sha256(v1.read_bytes()).hexdigest())
        self.assertEqual(v2['threshold']['recommended_primary'],700)
        self.assertIsNone(v2['threshold']['approved_primary']);self.assertFalse(v2['training_enabled'])
        self.assertIn('no performance',v2['revision_basis'])

    def test_35_other_query_chemistry_cannot_change_query_rows(self):
        model=RoleMaskedPPI().double().eval();h=model.forward(self.graph,700,'G_realPPI')['protein_h'].detach()
        before=model.query_readout(self.query,h)['representation']
        changed={k:v.copy() for k,v in self.query.items()};i=int(np.flatnonzero(changed['masks'][:,0])[0])
        changed['chemistry'][i]+=37
        after=model.query_readout(changed,h)['representation'];other=[j for j in range(len(after)) if j!=i]
        torch.testing.assert_close(before[other],after[other],rtol=1e-12,atol=1e-12)


if __name__=='__main__':unittest.main(verbosity=2)
