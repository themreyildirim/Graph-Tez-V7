"""WP10 tasarımına yönelik etiket-kör yapı envanteri; PyG nesnesi/model/fit üretmez."""
import importlib.util
import json
import numpy as np
import pandas as pd
from wp04_chemistry import Chem, rdBase, parse_smiles, identity
from wp09_train import ROOT, sha, write_json

QA=ROOT/'reports/qa/WP10/design_v1'
SCHEMA={
    'atom':{'element':['C','N','O','F','P','S','Cl','Br','I','OTHER'],
        'total_degree':[0,1,2,3,4,5,6,'OTHER'],'formal_charge':[-2,-1,0,1,2,'OTHER'],
        'total_H':[0,1,2,3,4,'OTHER'],'hybridization':['SP','SP2','SP3','SP3D','SP3D2','OTHER'],
        'aromatic':['bool'],'in_ring':['bool'],'CIP_state':['R','S','UNASSIGNED_POTENTIAL','NONE','OTHER'],
        'isotope_specified':['bool']},
    'bond':{'bond_type':['SINGLE','DOUBLE','TRIPLE','AROMATIC','OTHER'],
        'stereo':['STEREONONE','STEREOANY','STEREOZ','STEREOE','STEREOCIS','STEREOTRANS','OTHER'],
        'conjugated':['bool'],'in_ring':['bool']}}


def feature_dimensions():
    return {key:sum(len(values) for values in block.values()) for key,block in SCHEMA.items()}


def parameter_count(k):
    # Önerilen modülün cebirsel sayımı; model kurulmaz.
    atom_dim,bond_dim=feature_dimensions().values()
    molecular=(atom_dim*16+16)+16*16+16*16+bond_dim*16+(16*8+8)
    return {'train_PT':int(k),'WP09_total':3920+142*int(k),'proposed_molecular_branch':molecular,
        'proposed_total':3920+molecular+151*int(k),'proposed_increment':molecular+9*int(k)}


def inspect_structure(source,old):
    mol,status=parse_smiles(source.raw_smiles)
    if status!='valid':raise ValueError(f'{source.id}: {status}')
    observed=identity(mol)
    for key in ['atom_count','bond_count','components','chiral_unassigned','double_stereo_unassigned']:
        assert observed[key]==getattr(old,key),(source.id,key)
    assert observed['rdkit_inchikey']==old.rdkit_inchikey==source.raw_inchikey
    assert source.cid==old.cid==source.bridge_cid
    assert observed['rdkit_isomeric_smiles']==old.rdkit_isomeric_smiles
    adjacency=np.zeros((mol.GetNumAtoms(),mol.GetNumAtoms()),dtype=bool)
    for bond in mol.GetBonds():
        i,j=bond.GetBeginAtomIdx(),bond.GetEndAtomIdx();adjacency[i,j]=adjacency[j,i]=True
    assert np.all(adjacency==adjacency.T) and not np.diag(adjacency).any()
    assert adjacency.sum()==2*mol.GetNumBonds()
    return {'id':source.id,'name':source.name,'cid':source.cid,'source_kind':source.source_kind,
        'technical_graph_possible':True,'strict_QC_pass_unchanged':old.strict_qc_pass,
        'review_flags':old.review_flags if isinstance(old.review_flags,str) else '',
        'proposed_atom_modality_eligible_PENDING_APPROVAL':bool(old.strict_qc_pass),
        'atoms':mol.GetNumAtoms(),'bonds':mol.GetNumBonds(),'directed_edges_if_materialized':int(adjacency.sum()),
        'components':len(Chem.GetMolFrags(mol)),'unassigned_atom_stereo':old.chiral_unassigned,
        'unassigned_double_stereo':old.double_stereo_unassigned,
        'max_degree':int(adjacency.sum(axis=1).max()),'source_SMILES_sha256':__import__('hashlib').sha256(source.raw_smiles.encode()).hexdigest()},mol


def main():
    QA.mkdir(parents=True,exist_ok=True)
    if (QA/'feasibility_summary.json').exists():raise RuntimeError('Tasarım v1 zaten var; ezilmez')
    paths=['reports/qa/WP04/structure_sources.csv','reports/qa/WP04/structure_validation.csv',
        'reports/qa/WP04/chemical_features_clean.csv','reports/qa/WP09/training_v1/model_fit_summary.csv',
        'reports/qa/WP08/experimental_preparation/frozen_split_manifest.json',
        'docs/plan/ROADMAP_V7.md','AGENTS.md']
    write_json(QA/'input_manifest.json',{p:sha(ROOT/p) for p in paths})
    source=pd.read_csv(ROOT/paths[0]);old=pd.read_csv(ROOT/paths[1]).set_index('id')
    assert len(source)==62 and source.id.is_unique and set(source.id)==set(old.index)
    records=[];atoms=[];bonds=[]
    for row in source.itertuples():
        previous=old.loc[row.id];record,mol=inspect_structure(row,previous);records.append(record)
        for atom in mol.GetAtoms():
            atoms.append({'id':row.id,'element':atom.GetSymbol(),'total_degree':atom.GetTotalDegree(),
                'formal_charge':atom.GetFormalCharge(),'total_H':atom.GetTotalNumHs(),
                'hybridization':str(atom.GetHybridization()),'aromatic':atom.GetIsAromatic(),
                'in_ring':atom.IsInRing(),'isotope':atom.GetIsotope(),'radical_electrons':atom.GetNumRadicalElectrons()})
        for bond in mol.GetBonds():
            bonds.append({'id':row.id,'bond_type':str(bond.GetBondType()),'stereo':str(bond.GetStereo()),
                'conjugated':bond.GetIsConjugated(),'in_ring':bond.IsInRing()})
    table=pd.DataFrame(records);table.to_csv(QA/'molecular_graph_feasibility_all62.csv',index=False,encoding='utf-8-sig')
    table[~table.strict_QC_pass_unchanged].to_csv(QA/'QC_review_eight_preserved.csv',index=False,encoding='utf-8-sig')
    distributions=[]
    for kind,df in [('atom',pd.DataFrame(atoms)),('bond',pd.DataFrame(bonds))]:
        for column in df.columns.drop('id'):
            for value,count in df[column].value_counts(dropna=False).items():
                distributions.append({'kind':kind,'field':column,'value':str(value),'count':int(count)})
    pd.DataFrame(distributions).to_csv(QA/'raw_atom_bond_field_distributions.csv',index=False)
    fits=pd.read_csv(ROOT/paths[3]);pd.DataFrame([parameter_count(k) for k in sorted(fits.num_targets.unique())]).to_csv(QA/'parameter_budget_by_train_PT.csv',index=False)
    proposal={'version':'WP10-design-PROPOSED-v1','status':'AWAITING_USER_DESIGN_APPROVAL','training_enabled':False,
        'model_implemented':False,'graph_tensors_materialized':False,'roadmap_scope':'WP10: SMILES→atom/bond graph, RDKit→PyG Data, readout; small molecular GNN, may defer if insufficient',
        'source':'Existing WP04 DrugBank XML SMILES; PubChem CID bridge locally verified, no new live PubChem structure verification',
        'cohort_inventory':62,'proposed_atom_eligible':54,'QC_review_pending':8,'QC_changes':False,
        'all62_kept_in_inventory':True,'WP09_B2_eligibility_frozen':61,'Methenamine_abstains':True,
        'features':SCHEMA,'feature_dimensions':feature_dimensions(),
        'raw_stereo_metadata':['source_SMILES','raw_chiral_tag','CIP','bond_stereo','stereo_atoms','bond_direction'],
        'atom_index_is_identity_feature':False,'labels_in_molecule_data':False,
        'isotope_policy':'Store exact isotope in audit; proposed bool input only; nonzero isotope or radicals triggers separate review before use',
        'PyG_contract':{'x':'float32[N,44] proposed, not built','edge_index':'int64[2,2B] two directions, no self-loop','edge_attr':'float32[2B,14] proposed','num_nodes':'explicit N','y':'absent; supervision separate by frozen train PT','batch':'separate per-drug disjoint graphs; no cross-molecule edges'},
        'structure_policy':'No stereo completion, parent/fragment selection, neutralization, tautomer replacement, atom/bond deletion; implicit-H RDKit parsing as WP04',
        'molecular_encoder':'h0=ReLU(P_atom x); h1=h0+ReLU(S h0 + mean_j ReLU(U h0_j + V e_ji)); one layer, hidden16; isolated mean0',
        'readout':'all-atom mean then Linear16→8/ReLU; mask; no fragment ratio claim; QC excludes Gentamicin branch',
        'fusion':'late concat existing141 + masked molecular8 + atom_mask1 =150; linear head151K',
        'factorial_primary':['A0_P0','A0_P1','A1_P0','A1_P1'],
        'factorial_control':'same augmented architecture, input eligibility, frozen train/PT/seed/init per context; branches disabled by masks/empty PPI; fixed old WP09 is separate historical reference',
        'atom_contrast':'A1_P0−A0_P0 and A1_P1−A0_P1; optional interaction (A1P1−A0P1)−(A1P0−A0P0)',
        'PPI_contrast':'A0_P1−A0_P0 and A1_P1−A1_P0; same700 strict human graph',
        'null_secondary':'If authorized, use same fixed R0/R1/R2 and NA rules; no new graph search; equal metric mean, no score ensemble',
        'comparison':'Frozen paired54/own61 drug/fold/PT keys; keep same common-inner exclusions; no target reselection from full cohort',
        'fitting':'Future only after approval: same train-only transforms, fixed schema; no test-based architecture/epoch/seed selection; maintain source PT and proxy semantics',
        'optimizer_proposal':'Inherit WP09 AdamW lr.001/wd.001, max200/patience20/min_delta.0001, common-inner median epochs; no performance-driven search',
        'seed_proposal':20261106,'experiment_scope':'exploratory after baseline and WP09 results; no external/clinical validation',
        'remaining_gates':['Approve strict54 atom mask and keep eight review holds','Approve 44/14 schema, one-layer16/8 architecture and150 fusion','Approve factorial scope, common inner mask and optional null cost','Approve future implementation/encoder tests separately; training requires explicit authorization']}
    write_json(ROOT/'configs/WP10_design_PROPOSED_v1.json',proposal)
    methods=[{'title':'RDKit Book: aromaticity/stereochemistry','url':'https://www.rdkit.org/docs/RDKit_Book.html'},
        {'title':'PyG Data shapes','url':'https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.data.Data.html'},
        {'title':'PyG NNConv edge-conditioned messages (alternative, not proposed instantiated architecture)','url':'https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.NNConv.html'},
        {'title':'PyG global_mean_pool','url':'https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.pool.global_mean_pool.html'}]
    write_json(QA/'method_sources.json',{'checked_date':'2026-11-06','biological_data_downloaded':False,'sources':methods})
    summary={'source_records':len(table),'parse_and_local_key_match':len(table),'technical_graph_possible':int(table.technical_graph_possible.sum()),
        'QC_clear_proposed_atom_mask':int(table.strict_QC_pass_unchanged.sum()),'QC_review_pending':int((~table.strict_QC_pass_unchanged).sum()),
        'atoms_total':int(table.atoms.sum()),'bonds_total':int(table.bonds.sum()),'atoms_min':int(table.atoms.min()),'atoms_max':int(table.atoms.max()),
        'multi_component_records':int(table.components.gt(1).sum()),'isotope_nonzero_atoms':sum(a['isotope']!=0 for a in atoms),'radical_atoms':sum(a['radical_electrons']!=0 for a in atoms),
        'rdkit':rdBase.rdkitVersion,'PyG_import_available':importlib.util.find_spec('torch_geometric') is not None,
        'feature_dimensions_PROPOSED':feature_dimensions(),'model_constructed':False,'training_or_optimizer':False,'production_graph_tensors':False}
    write_json(QA/'feasibility_summary.json',summary);print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
