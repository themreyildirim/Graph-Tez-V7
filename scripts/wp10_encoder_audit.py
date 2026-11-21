"""Etiket-kör gerçek/sentetik forward,gradient ve 40 bağlam teknik audit'i."""
import json
import platform
import sys
import numpy as np
import pandas as pd
from wp10_molecular_graph import ROOT,QA,Chem,torch,Batch,load_store,build_graph,parse_smiles,numeric_digest,graph_arrays
from wp10_molecular_encoder import BondAwareMolecularEncoder,initialized_model,model_digest,load_context,VARIANTS
from wp09_train import sha,write_json


def preserve():
    previous=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    errors=[p for p,h in previous.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    if errors:raise AssertionError(errors)
    return len(previous)


def remove_pair(data):
    out=data.clone();i,j=out.edge_index[:,0];e=out.edge_index
    keep=~(((e[0]==i)&(e[1]==j))|((e[0]==j)&(e[1]==i)))
    out.edge_index=e[:,keep];out.edge_attr=out.edge_attr[keep];return out


def main():
    if (QA/'technical_audit_complete.json').exists():raise RuntimeError('Teknik kanıt zaten var;ezilmez')
    protected=preserve();torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    store=load_store();source=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv').set_index('id')
    import torch_geometric
    from wp04_chemistry import rdBase
    if torch_geometric.__version__!='2.8.0':raise RuntimeError('Approved real PyG2.8.0 runtime required')
    write_json(QA/'environment.json',{'python':platform.python_version(),'torch':torch.__version__,'PyG':torch_geometric.__version__,
        'RDKit':rdBase.rdkitVersion,'CPU_threads':1,'deterministic_algorithms':True,'device':'CPU','optimizer_steps':0})
    model=initialized_model();initial_hash=model_digest(model)
    np.savez_compressed(QA/'UNTRAINED_initial_state.npz',**{k:t.detach().numpy() for k,t in model.state_dict().items()})
    write_json(QA/'UNTRAINED_initial_state.json',{'version':'WP10-molecular-encoder-v1','seed':20261106,'state_sha256':initial_hash,
        'parameters':sum(p.numel() for p in model.parameters()),'molecular_parameters':sum(p.numel() for p in model.molecular.parameters()),
        'trained':False,'PT_head':False,'optimizer_steps':0,'purpose':'initialization reproducibility only; NOT a fitted ADR model'})
    perm=[];rng=np.random.default_rng(20261106);encoder=initialized_model(dtype=torch.float64).molecular.eval()
    for d in sorted(store.graphs):
        mol,_=parse_smiles(source.loc[d,'raw_smiles']);order=rng.permutation(mol.GetNumAtoms()).tolist()
        remapped=Chem.RenumberAtoms(mol,order);g,raw=build_graph(remapped)
        with torch.no_grad():
            a=encoder(Batch.from_data_list([store.graphs[d]]))['molecular_h'];b=encoder(Batch.from_data_list([g]))['molecular_h']
        error=float((a-b).abs().max());assert error<1e-12
        perm.append({'id':d,'max_absolute_readout_error':error,'pass_atol_1e_12':True,'permutation_sha256':numeric_digest({'permutation':np.array(order,dtype=np.int64)})})
    pd.DataFrame(perm).to_csv(QA/'permutation_all62.csv',index=False)
    proof=[]
    for d in ['DB00601','DB00537','DB01060']:
        g=store.graphs[d];m=initialized_model(dtype=torch.float64).molecular
        before=numeric_digest(m.state_dict());original=m(Batch.from_data_list([g]))['molecular_h']
        removed=m(Batch.from_data_list([remove_pair(g)]))['molecular_h']
        changed=g.clone();original_type=int(changed.edge_attr[0,:5].argmax());changed.edge_attr[:2,:5]=0;changed.edge_attr[:2,(original_type+1)%4]=1
        altered=m(Batch.from_data_list([changed]))['molecular_h']
        original.sum().backward()  # Etiket/loss/optimizer yok;temsil toplamının türevi.
        atom_grad=float(m.atom_message.weight.grad.norm());bond_grad=float(m.bond_message.weight.grad.norm())
        delta=float((original-removed).detach().norm());bond_delta=float((original-altered).detach().norm())
        assert atom_grad>0 and bond_grad>0 and delta>0 and bond_delta>0 and before==numeric_digest(m.state_dict())
        proof.append({'id':d,'name':source.loc[d,'name'],'edge_removed_output_L2':delta,'bond_type_perturbed_output_L2':bond_delta,
            'atom_message_gradient_norm':atom_grad,'bond_message_gradient_norm':bond_grad,'optimizer_steps':0,'weights_unchanged':True,
            'perturbation_semantics':'feature-level software probe; NOT a validated alternative chemical structure'})
    pd.DataFrame(proof).to_csv(QA/'real_molecular_forward_gradient.csv',index=False)
    # Sayısal olarak ayırt edici CCO;beklenen değerler testten bağımsız açıkça kaydedilir.
    m=BondAwareMolecularEncoder().double()
    with torch.no_grad():
        for p in m.parameters():p.zero_()
        m.projection.weight[0,0]=1;m.projection.weight[0,2]=2;m.self_update.weight[0,0]=.5
        m.atom_message.weight[0,0]=.75;m.bond_message.weight[0,0]=1;m.bond_message.weight[0,1]=3;m.readout.weight[0,0]=1
    mol,_=parse_smiles('CCO');g,_=build_graph(mol);out=m(Batch.from_data_list([g]));out['molecular_h'].sum().backward()
    synthetic={'smiles':'CCO','node_h0_first':out['node_h0'][:,0].detach().tolist(),'node_h_first':out['node_h'][:,0].detach().tolist(),
        'graph_readout_first':float(out['molecular_h'][0,0].detach()),'expected_readout':3.875,
        'd_output_d_atom_message_00':float(m.atom_message.weight.grad[0,0]),'expected_atom_gradient':7/6,
        'd_output_d_bond_message_single_00':float(m.bond_message.weight.grad[0,0]),'expected_bond_gradient':1.0,'optimizer_steps':0}
    assert synthetic['graph_readout_first']==3.875 and abs(synthetic['d_output_d_atom_message_00']-7/6)<1e-12
    write_json(QA/'synthetic_analytic_proof.json',synthetic)
    contexts=pd.read_csv(ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv')
    audits=[];scope=[];input_hashes=json.loads((QA/'input_manifest.json').read_text(encoding='utf-8'))
    for context,part in contexts.groupby('context',sort=True):
        row=part.iloc[0];seed=20261106+10000*int(row.protocol=='stress')+100*int(row.outer_fold)+int(row.inner_fold)
        m=initialized_model(seed);init=model_digest(m);graph,query,tm,qm=load_context(context,store)
        for kind in ['train','query']:
            path=f'reports/qa/WP09/design_v1/folds/{context}_{kind}.npz';input_hashes[path]=sha(ROOT/path)
        for variant in VARIANTS:
            events=[];hook=m.base.protein.message.register_forward_pre_hook(lambda module,args:events.append(float(args[0].detach().norm())))
            with torch.no_grad():
                train=m.encode_train(graph,tm,variant);cache=train['cache'];saved=cache.protein_h.clone()
                result=m.encode_query(graph,query,qm,cache)
            hook.remove()
            assert m.head is None and train['logits'] is None and result['logits'] is None
            assert torch.isfinite(train['representation']).all() and torch.isfinite(result['representation']).all()
            assert model_digest(m)==init and torch.equal(saved,cache.protein_h)
            assert train['representation'].shape==(len(tm.ids),150) and result['representation'].shape==(len(qm.ids),150)
            if variant[-1]=='0':assert events[0]==0
            else:assert events[0]>0
            if variant[1]=='0':assert train['molecular_block'].abs().sum()==0 and result['molecular_block'].abs().sum()==0
            audits.append({'context':context,'variant':variant,'seed':seed,'initial_state_sha256':init,
                'train_drugs':len(tm.ids),'query_drugs':len(qm.ids),'train_dim':150,'query_dim':150,'base_dim':141,'molecular_dim':8,
                'train_active_atom_mask':int(train['effective_atom_mask'].sum()),'query_active_atom_mask':int(result['effective_atom_mask'].sum()),
                'train_PPI_neighbor_input_norm':events[0],'train_cache_unchanged':True,'model_state_unchanged':True,'PT_head':False,'optimizer_steps':0})
        scope.append({'context':context,'train_drug_ids':json.dumps(tm.ids),'query_drug_ids':json.dumps(qm.ids),
            'train_atom_mask':json.dumps(tm.atom_mask.tolist()),'query_atom_mask':json.dumps(qm.atom_mask.tolist()),
            'train_bundle_numeric_sha256':numeric_digest(graph),'query_bundle_numeric_sha256':numeric_digest(query),'PT_labels_read':False})
    pd.DataFrame(audits).to_csv(QA/'integration_forward_40contexts_4variants.csv',index=False)
    pd.DataFrame(scope).to_csv(QA/'train_query_scope_manifest.csv',index=False)
    write_json(QA/'input_manifest.json',input_hashes)
    counts=[]
    for k in [0,3,158,326]:
        m=initialized_model(num_targets=None if k==0 else k);count=sum(p.numel() for p in m.parameters())
        assert count==5512+151*k
        counts.append({'K_synthetic_shape_only':k,'actual_parameters':count,'expected_parameters':5512+151*k,'head_used_on_real_data':False})
    pd.DataFrame(counts).to_csv(QA/'actual_parameter_counts.csv',index=False)
    write_json(QA/'technical_audit_complete.json',{'status':'PASS','version':'WP10-molecular-encoder-v1','real_PyG_graphs':62,
        'QC_atom_enabled':54,'QC_atom_disabled':8,'atoms':2061,'undirected_bonds':2219,'directed_edges':4438,
        'permutation_cases':62,'maximum_permutation_error':max(r['max_absolute_readout_error'] for r in perm),
        'real_gradient_edge_cases':3,'contexts':40,'variant_forward_cases':160,'representation_dim':150,'PT_head_on_real_data':False,
        'real_PT_labels_read':False,'optimizer_steps':0,'model_fit':False,'outer_test_PT_scores':False,
        'prior_files_verified':preserve(),'initialization_state_sha256':initial_hash,'molecular_parameters':1592,'base_and_molecule_parameters':5512})
    print('PASS:62 PyG graphs,62 permutations,3 real gradient probes,40x4 contexts;no optimizer/PT scores')


if __name__=='__main__':main()
