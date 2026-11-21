"""Sentetik kimya→gerçek62 graf→etiketsiz entegrasyon;optimizer/PT eğitimi yok."""
from pathlib import Path
import sys,json,copy,unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp10_molecular_graph import (QA,Chem,torch,Data,Batch,build_graph,parse_smiles,load_store,
    validate_graph,graph_arrays,numeric_digest,slices,SCHEMA)
from wp10_molecular_encoder import (BondAwareMolecularEncoder,initialized_model,model_digest,load_context,validate_context_bundles,VARIANTS)


def graph(smiles):
    mol,status=parse_smiles(smiles)
    if status!='valid':raise ValueError(status)
    return build_graph(mol)[0]


def controlled_encoder():
    m=BondAwareMolecularEncoder().double()
    with torch.no_grad():
        for p in m.parameters():p.zero_()
        m.projection.weight[0,0]=1;m.projection.weight[0,2]=2
        m.self_update.weight[0,0]=.5;m.atom_message.weight[0,0]=.75
        m.bond_message.weight[0,0]=1;m.bond_message.weight[0,1]=3
        m.readout.weight[0,0]=1
    return m


def without_pair(data,i,j):
    result=data.clone();e=result.edge_index
    keep=~(((e[0]==i)&(e[1]==j))|((e[0]==j)&(e[1]==i)))
    result.edge_index=e[:,keep];result.edge_attr=result.edge_attr[keep];return result


class MolecularEncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
        cls.store=load_store();cls.source=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv').set_index('id')

    def test_01_synthetic_one_hot_charge_H_and_element(self):
        d=graph('[NH4+]');s=slices('atom')
        self.assertEqual(d.x[0,s['element']][1],1);self.assertEqual(d.x[0,s['formal_charge']][3],1)
        self.assertEqual(d.x[0,s['total_H']][4],1);self.assertEqual(d.edge_index.shape,(2,0))

    def test_02_aromatic_atoms_and_bonds(self):
        d=graph('c1ccccc1');self.assertEqual(d.num_nodes,6);self.assertEqual(d.num_edges,12)
        self.assertTrue(d.x[:,slices('atom')['aromatic']].eq(1).all())
        self.assertTrue(d.edge_attr[:,slices('bond')['bond_type']][:,3].eq(1).all())

    def test_03_single_double_triple_bond_types(self):
        for smi,index in [('CC',0),('C=C',1),('C#N',2)]:
            self.assertTrue(graph(smi).edge_attr[:,index].eq(1).all())

    def test_04_CIP_R_S_and_unspecified_not_none(self):
        def state(smi):
            m,_=parse_smiles(smi);d,raw=build_graph(m);return d,raw['atoms'][1]['CIP_state']
        a,aa=state('C[C@H](O)F');b,bb=state('C[C@@H](O)F');u,uu=state('CC(O)F')
        self.assertEqual({aa,bb},{'R','S'});self.assertEqual(uu,'UNASSIGNED_POTENTIAL')
        self.assertFalse(torch.equal(a.x,b.x));self.assertTrue(torch.equal(a.edge_index,b.edge_index))

    def test_05_E_Z_unknown_and_raw_bond_direction(self):
        results=[]
        for smi in ['F/C=C/F','F/C=C\\F','FC=CF']:
            m,_=parse_smiles(smi);d,raw=build_graph(m);results.append([r for r in raw['bonds'] if r['bond_type']=='DOUBLE'][0])
        self.assertEqual({results[0]['stereo'],results[1]['stereo']},{'STEREOE','STEREOZ'})
        self.assertEqual(results[2]['stereo'],'STEREOANY');self.assertEqual(results[2]['raw_bond_stereo'],'STEREONONE')
        m,_=parse_smiles('F/C=C/F');d,raw=build_graph(m)
        self.assertTrue(any(b['raw_bond_direction']!='NONE' for b in raw['bonds']))
        for b in raw['bonds']:torch.testing.assert_close(d.edge_attr[b['forward_column']],d.edge_attr[b['reverse_column']],rtol=0,atol=0)

    def test_06_unknown_element_and_isotope(self):
        d=graph('[13CH4].[Xe]');self.assertEqual(d.x[0,slices('atom')['isotope_specified']].item(),1)
        self.assertEqual(d.x[1,slices('atom')['element']][-1],1);self.assertEqual(d.num_nodes,2)

    def test_07_analytic_forward_uses_neighbor_and_bond_features(self):
        d=graph('CCO');m=controlled_encoder();b=Batch.from_data_list([d])
        out=m(b);self.assertAlmostEqual(out['molecular_h'][0,0].item(),3.875,places=12)
        torch.testing.assert_close(out['node_h'][:,0],torch.tensor([3.25,3.625,4.75],dtype=torch.float64),rtol=0,atol=1e-12)
        removed=without_pair(d,1,2);self.assertAlmostEqual(m(Batch.from_data_list([removed]))['molecular_h'][0,0].item(),19/6,places=12)
        changed=d.clone();mask=((changed.edge_index[0]==1)&(changed.edge_index[1]==2))|((changed.edge_index[0]==2)&(changed.edge_index[1]==1))
        changed.edge_attr[mask,0]=0;changed.edge_attr[mask,1]=1
        self.assertAlmostEqual(m(Batch.from_data_list([changed]))['molecular_h'][0,0].item(),4.875,places=12)

    def test_08_analytic_message_gradient(self):
        m=controlled_encoder();m(Batch.from_data_list([graph('CCO')]))['molecular_h'].sum().backward()
        self.assertAlmostEqual(m.atom_message.weight.grad[0,0].item(),7/6,places=12)
        self.assertAlmostEqual(m.bond_message.weight.grad[0,0].item(),1,places=12)

    def test_09_isolated_atom_has_zero_neighbor_mean(self):
        m=controlled_encoder();out=m(Batch.from_data_list([graph('C')]))
        self.assertEqual(float(out['neighbor_mean'].abs().sum()),0)
        self.assertAlmostEqual(out['molecular_h'][0,0].item(),1.5,places=12)

    def test_10_all62_Data_identity_counts_and_no_labels(self):
        old=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv').set_index('id')
        self.assertEqual(len(self.store.graphs),62)
        for d,g in self.store.graphs.items():
            self.assertTrue(validate_graph(g));self.assertEqual(g.num_nodes,old.loc[d,'atom_count']);self.assertEqual(g.num_edges,2*old.loc[d,'bond_count'])
            self.assertEqual(g.x.shape[1],44);self.assertEqual(g.edge_attr.shape[1],14)
            self.assertEqual(self.store.registry[d]['cid'],int(self.source.loc[d,'cid']))
            self.assertEqual(self.store.registry[d]['source_InChIKey'],old.loc[d,'rdkit_inchikey'])

    def test_11_exact54_8_and_Gentamicin_components(self):
        self.assertEqual(sum(m['atom_eligible'] for m in self.store.registry.values()),54)
        g=self.store.graphs['DB00798'];self.assertEqual(g.num_nodes,105)
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        adjacency=coo_matrix((np.ones(g.num_edges),(g.edge_index[0],g.edge_index[1])),shape=(g.num_nodes,g.num_nodes))
        self.assertEqual(connected_components(adjacency,directed=False)[0],3)
        self.assertFalse(self.store.registry['DB06799']['atom_eligible'])

    def test_12_all_reverse_edge_alignment(self):
        for d,meta in self.store.registry.items():
            g=self.store.graphs[d]
            for bond in meta['raw_stereo_metadata']['bonds']:
                a,b=bond['forward_column'],bond['reverse_column']
                self.assertEqual(g.edge_index[:,a].tolist(),[bond['begin_atom'],bond['end_atom']])
                self.assertEqual(g.edge_index[:,b].tolist(),[bond['end_atom'],bond['begin_atom']])
                torch.testing.assert_close(g.edge_attr[a],g.edge_attr[b],rtol=0,atol=0)

    def test_13_real_permutation_invariance_all62(self):
        m=initialized_model(dtype=torch.float64).molecular.eval();rng=np.random.default_rng(20261106)
        for d in self.source.index:
            mol,_=parse_smiles(self.source.loc[d,'raw_smiles']);permuted=Chem.RenumberAtoms(mol,rng.permutation(mol.GetNumAtoms()).tolist())
            a,_=build_graph(mol);b,_=build_graph(permuted)
            with torch.no_grad():x=m(Batch.from_data_list([a]))['molecular_h'];y=m(Batch.from_data_list([b]))['molecular_h']
            torch.testing.assert_close(x,y,rtol=1e-12,atol=1e-12)

    def test_14_real_Linezolid_edge_and_bond_type_forward(self):
        g=self.store.graphs['DB00601'];m=initialized_model(dtype=torch.float64).molecular
        # Feature-level perturbation; not a chemically validated replacement molecule.
        changed=g.clone();changed.edge_attr[:2,:5]=0;changed.edge_attr[:2,1]=1
        with torch.no_grad():
            a=m(Batch.from_data_list([g]))['molecular_h'];b=m(Batch.from_data_list([without_pair(g,*g.edge_index[:,0].tolist())]))['molecular_h'];c=m(Batch.from_data_list([changed]))['molecular_h']
        self.assertGreater(float((a-b).norm()),1e-9);self.assertGreater(float((a-c).norm()),1e-9)

    def test_15_real_message_and_bond_gradients(self):
        m=initialized_model(dtype=torch.float64).molecular
        m(self.store.make_batch(['DB00601','DB00537','DB01060']).batch)['molecular_h'].sum().backward()
        self.assertGreater(float(m.atom_message.weight.grad.norm()),0);self.assertGreater(float(m.bond_message.weight.grad.norm()),0)

    def test_16_molecule_batch_independence(self):
        m=initialized_model(dtype=torch.float64).molecular
        with torch.no_grad():
            a=m(self.store.make_batch(['DB00601']).batch)['molecular_h'];b=m(self.store.make_batch(['DB00601','DB00798']).batch)['molecular_h']
        torch.testing.assert_close(a[0],b[0],rtol=1e-12,atol=1e-12)

    def test_17_rebuild_exact_tensor_hashes(self):
        for d in ['DB00601','DB00798','DB01165']:
            mol,_=parse_smiles(self.source.loc[d,'raw_smiles']);g,_=build_graph(mol)
            self.assertEqual(numeric_digest(graph_arrays(g)),self.store.registry[d]['graph_tensor_sha256'])

    def test_18_same_init_hash_and_parameter_counts(self):
        a=initialized_model();b=initialized_model()
        self.assertEqual(model_digest(a),model_digest(b));self.assertEqual(sum(p.numel() for p in a.molecular.parameters()),1592)
        self.assertEqual(sum(p.numel() for p in a.parameters()),5512)
        for k in [3,158,326]:self.assertEqual(sum(p.numel() for p in initialized_model(num_targets=k).parameters()),5512+151*k)

    def test_19_four_variants_dimensions_and_closed_atom_branch(self):
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model()
        for variant in VARIANTS:
            with torch.no_grad():a=model.encode_train(g,tm,variant);b=model.encode_query(g,q,qm,a['cache'])
            self.assertEqual(a['representation'].shape,(len(g['drug_ids']),150));self.assertIsNone(a['logits']);self.assertIsNone(b['logits'])
            if variant[1]=='0':self.assertEqual(float(a['molecular_block'].abs().sum()),0);self.assertFalse(a['effective_atom_mask'].any())
            self.assertEqual(a['effective_atom_mask'].tolist(),(tm.atom_mask & (variant[1]=='1')).tolist())

    def test_20_PPI_off_hook_observes_zero_neighbors(self):
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model();events=[]
        h=model.base.protein.message.register_forward_pre_hook(lambda module,args:events.append(float(args[0].detach().norm())))
        model.encode_train(g,tm,'A1P0');self.assertEqual(events[-1],0)
        model.encode_train(g,tm,'A1P1');self.assertGreater(events[-1],0);h.remove()

    def test_21_query_mutation_isolated_from_other_queries_cache_and_state(self):
        from wp10_molecular_graph import MolecularInput
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model(dtype=torch.float64)
        with torch.no_grad():
            train=model.encode_train(g,tm,'A1P1');cache=train['cache'];saved=cache.protein_h.clone();before=model_digest(model)
            original=model.encode_query(g,q,qm,cache)['representation']
            altered=qm.batch.clone();drug=int(torch.nonzero(qm.atom_mask)[0]);node=int(altered.ptr[drug]);values=altered.x[node,:10];index=int(values.argmax());values.zero_();values[(index+1)%10]=1
            changed=model.encode_query(g,q,MolecularInput(qm.ids,altered,qm.atom_mask.clone()),cache)['representation']
        keep=np.arange(len(qm.ids))!=drug
        torch.testing.assert_close(original[keep],changed[keep],rtol=0,atol=1e-12)
        self.assertGreater(float((original[drug]-changed[drug]).norm()),1e-9)
        torch.testing.assert_close(cache.protein_h,saved,rtol=0,atol=0);self.assertEqual(before,model_digest(model))

    def test_22_train_query_and_PT_injection_rejected(self):
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model()
        with self.assertRaises(ValueError):model.encode_train(g,qm,'A1P1')
        injected={**g,'PT_labels':np.zeros((1,1))}
        with self.assertRaises(ValueError):model.encode_train(injected,tm,'A1P1')
        bad=self.store.graphs['DB00601'].clone();bad.y=torch.ones(1)
        with self.assertRaises(ValueError):validate_graph(bad)
        with self.assertRaises(TypeError):model.encode_train(g,tm,'A1P1',labels={'FAKE':1})
        bad={k:a.copy() for k,a in g.items()};bad['drug_ids'][0]=q['drug_ids'][0]
        with self.assertRaises(ValueError):validate_context_bundles('primary_o01_final',bad,q)
        badq={k:a.copy() for k,a in q.items()};badq['split'][:]='train'
        with self.assertRaises(ValueError):validate_context_bundles('primary_o01_final',g,badq)

    def test_23_frozen_QC_mask_cannot_be_opened(self):
        from wp10_molecular_graph import MolecularInput
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model()
        bad=tm.atom_mask.clone();bad[0]=~bad[0]
        with self.assertRaises(ValueError):model.encode_train(g,MolecularInput(tm.ids,tm.batch,bad),'A1P1')

    def test_24_train_cache_bound_to_graph_and_model(self):
        g,q,tm,qm=load_context('primary_o01_final',self.store);model=initialized_model()
        cache=model.encode_train(g,tm,'A1P1')['cache'];bad={k:a.copy() for k,a in g.items()};bad['protein_x'][0,0]+=1
        with self.assertRaises(ValueError):model.encode_query(bad,q,qm,cache)
        with torch.no_grad():next(model.parameters()).add_(.001)
        with self.assertRaises(ValueError):model.encode_query(g,q,qm,cache)

    def test_25_Methenamine_abstention_Tobramycin_no_protein(self):
        for context in ['primary_o01_final','stress_o01_final']:
            g,q,tm,qm=load_context(context,self.store);model=initialized_model()
            with torch.no_grad():t=model.encode_train(g,tm,'A1P1');v=model.encode_query(g,q,qm,t['cache'])
            for block,out in [(g,t),(q,v)]:
                for d in ['DB06799','DB00684']:
                    if d not in block['drug_ids']:continue
                    i=list(block['drug_ids']).index(d)
                    if d=='DB06799':self.assertFalse(out['eligible'][i]);self.assertFalse(out['effective_atom_mask'][i])
                    else:self.assertTrue(out['eligible'][i]);self.assertFalse(block['masks'][i,1:].any())

    def test_26_frozen40_context_memberships_and_no_targets(self):
        parts=pd.read_csv(ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv')
        for context in sorted(parts.context.unique()):
            g,q,tm,qm=load_context(context,self.store)
            self.assertFalse(set(tm.ids)&set(qm.ids));self.assertEqual(set(tm.ids)|set(qm.ids),set(self.store.graphs))

    def test_27_corrupt_tensors_and_reverse_alignment_rejected(self):
        g=self.store.graphs['DB00601'].clone();g.edge_index=g.edge_index.reshape(-1)
        with self.assertRaises(ValueError):validate_graph(g)
        g=self.store.graphs['DB00601'].clone();g.x=g.x[:,:43]
        with self.assertRaises(ValueError):validate_graph(g)
        g=self.store.graphs['DB00601'].clone();g.edge_attr[0,:5]=0;g.edge_attr[0,1]=1
        with self.assertRaises(ValueError):validate_graph(g)
        g=self.store.graphs['DB00601'].clone();g.x[0,0]=float('nan')
        with self.assertRaises(ValueError):validate_graph(g)

    def test_28_prior_artifacts_and_installed_PyG_unchanged(self):
        from wp09_train import sha
        import torch_geometric
        self.assertEqual(torch_geometric.__version__,'2.8.0')
        previous=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
        self.assertEqual([], [p for p,h in previous.items() if sha(ROOT/p)!=h])


if __name__=='__main__':unittest.main(verbosity=2)
