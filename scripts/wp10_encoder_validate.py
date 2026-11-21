"""Son salt okunur kaynak/şema/başlangıç/notebook/koruma denetimi."""
import ast,json,re
import nbformat
import numpy as np
import pandas as pd
from wp10_molecular_graph import ROOT,QA,torch,Chem,load_store,parse_smiles,build_graph,graph_arrays,numeric_digest
from wp10_molecular_encoder import initialized_model,model_digest
from wp10_encoder_audit import preserve
from wp09_train import sha,write_json


def main():
    previous=preserve();store=load_store()
    source=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv').set_index('id')
    checked=0
    for d in sorted(store.graphs):
        mol,status=parse_smiles(source.loc[d,'raw_smiles']);assert status=='valid'
        data,_=build_graph(mol)
        assert numeric_digest(graph_arrays(data))==store.registry[d]['graph_tensor_sha256']
        assert store.registry[d]['source_SMILES']==source.loc[d,'raw_smiles']
        assert store.registry[d]['cid']==source.loc[d,'cid']
        assert set(data.keys())=={'x','edge_index','edge_attr','num_nodes'}
        checked+=1
    frame=pd.read_csv(QA/'molecular_graph_QA_all62.csv')
    totals={'graphs':len(frame),'atom_mask_true':int(frame.atom_eligible.sum()),'atom_mask_false':int((~frame.atom_eligible).sum()),
        'atoms':int(frame.atoms.sum()),'bonds':int(frame.bonds.sum()),'directed_edges':int(frame.directed_edges.sum())}
    assert list(totals.values())==[62,54,8,2061,2219,4438]
    assert set(frame.id)==set(store.graphs)==set(source.index)
    assert frame.PyG_validate.all() and frame.identity_match.all() and not frame.y_present.any()
    assert len(list((QA/'graphs').glob('*.npz')))==62
    old=json.loads((QA/'prior_artifacts_sha256.json').read_text(encoding='utf-8'))
    old_models={p for p in old if p.startswith('models/')}
    assert old_models=={p.relative_to(ROOT).as_posix() for p in (ROOT/'models').rglob('*') if p.is_file()}
    with np.load(QA/'UNTRAINED_initial_state.npz',allow_pickle=False) as a:arrays={k:a[k].copy() for k in a.files}
    model=initialized_model();metadata=json.loads((QA/'UNTRAINED_initial_state.json').read_text(encoding='utf-8'))
    assert numeric_digest(arrays)==metadata['state_sha256']==model_digest(model)
    assert model.head is None and sum(p.numel() for p in model.parameters())==5512 and not metadata['trained']
    for k,value in model.state_dict().items():assert np.array_equal(value.detach().numpy(),arrays[k])
    cases=pd.read_csv(QA/'integration_forward_40contexts_4variants.csv')
    assert len(cases)==160 and cases.groupby('context').variant.nunique().eq(4).all()
    assert cases.groupby('context').initial_state_sha256.nunique().eq(1).all()
    assert cases.optimizer_steps.eq(0).all() and not cases.PT_head.any()
    assert cases.train_dim.eq(150).all() and cases.query_dim.eq(150).all()
    assert cases.train_cache_unchanged.all() and cases.model_state_unchanged.all()
    assert cases[cases.variant.str.endswith('0')].train_PPI_neighbor_input_norm.eq(0).all()
    assert cases[cases.variant.str.startswith('A0')].train_active_atom_mask.eq(0).all()
    inputs=json.loads((QA/'input_manifest.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/p)==h for p,h in inputs.items())
    config=json.loads((ROOT/'configs/WP10_encoder_IMPLEMENTED_v1.json').read_text(encoding='utf-8'))
    assert not config['training_enabled'] and not config['outer_PT_scoring_enabled'] and config['optimizer_steps']==0
    log=(QA/'test_results_context_guard.txt').read_text(encoding='utf-8-sig')
    tests=re.search(r'Ran 28 tests in ([0-9.]+)s',log);assert tests and log.rstrip().endswith('OK')
    notebook_path=ROOT/'notebooks/WP10_molecular_encoder.ipynb'
    book=nbformat.read(notebook_path,as_version=4);nbformat.validate(book)
    cells=[c for c in book.cells if c.cell_type=='code'];assert [c.execution_count for c in cells]==list(range(1,10))
    images=0;tables=0
    for c in cells:
        for out in c.outputs:
            assert out.output_type!='error' and not(out.output_type=='stream' and out.name=='stderr')
            images+=int('image/png' in out.get('data',{}));tables+=int('<table' in out.get('data',{}).get('text/html',''))
    assert images==6 and tables>=12
    figures=ROOT/'reports/figures/WP10/encoder_v1';assert len(list(figures.glob('*.png')))==6
    sources=[ROOT/'scripts'/name for name in ['wp10_molecular_graph.py','wp10_molecular_encoder.py','wp10_encoder_audit.py','wp10_encoder_notebook.py','wp10_encoder_report.py','wp10_encoder_validate.py']]
    for path in sources:
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                assert node.func.attr not in {'fit','fit_transform','step','AdamW','Adam','SGD'},(path,node.lineno)
    paths=sources+[ROOT/'tests/test_wp10_encoder.py',notebook_path,ROOT/'reports/WP10.md',ROOT/'reports/WP10_ENCODER_TRAINING_GATE.md',
        ROOT/'docs/plan/WP10_MOLECULAR_DATA_CONTRACT_v1.md',ROOT/'configs/WP10_encoder_IMPLEMENTED_v1.json',ROOT/'run_status.md']
    paths+=list(figures.glob('*.png'))
    paths +=[p for p in QA.rglob('*') if p.is_file() and p.name not in {'artifact_validation.json','final_artifact_manifest.json'}]
    write_json(QA/'final_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))})
    result={'status':'PASS','version':'WP10-molecular-encoder-v1','prior_artifacts_unchanged':previous,'graph_totals_calculated':totals,
        'source_rebuild_numeric_hash_matches':checked,'PyG_runtime':'2.8.0','new_technical_tests':28,'test_seconds':float(tests.group(1)),
        'context_variant_forward_cases':160,'PT_head_on_real_data':False,'optimizer_steps':0,'real_PT_training':False,
        'outer_PT_scores':False,'performance_tables':False,'molecular_parameters':1592,'headless_fusion_parameters':5512,
        'initial_model_state_hash':model_digest(model),'initial_snapshot_is_trained':False,'new_fitted_model_files':0,
        'notebook_executed_cells':9,'embedded_PNGs':images,'HTML_tables':tables,'PNG_files_visually_reviewed':6,
        'WP09_and_B0_B1_B2_unchanged':True,'source_QC_unchanged':True,'training_approval_required':True,'WP11_started':False}
    preserve();write_json(QA/'artifact_validation.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
