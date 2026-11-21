"""Etiketsiz WP04 yapılarını sabit 44/14 şemalı gerçek PyG Data'ya dönüştürür."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps/pyg'))
from wp04_chemistry import Chem,parse_smiles,identity
import torch
from torch_geometric.data import Data,Batch

QA=ROOT/'reports/qa/WP10/encoder_v1'
DESIGN=ROOT/'configs/WP10_design_PROPOSED_v1.json'
SCHEMA=json.loads(DESIGN.read_text(encoding='utf-8'))['features']


def schema_columns(kind):
    return [field if values==['bool'] else f'{field}={value}' for field,values in SCHEMA[kind].items() for value in values]


def slices(kind):
    result={};offset=0
    for field,values in SCHEMA[kind].items():result[field]=slice(offset,offset+len(values));offset+=len(values)
    return result


def vector(kind,values):
    if set(values)!=set(SCHEMA[kind]):raise ValueError('Feature allowlist mismatch')
    output=[]
    for field,categories in SCHEMA[kind].items():
        value=values[field]
        if categories==['bool']:output.append(float(bool(value)))
        else:
            selected=value if value in categories else 'OTHER'
            output.extend(float(category==selected) for category in categories)
    return output


def build_graph(mol):
    """Yalnız Mol alır; kimlik/QC/etiket içermez. Kaynak Mol değiştirilmez."""
    mol=Chem.Mol(mol)
    Chem.AssignStereochemistry(mol,cleanIt=True,force=True)
    stereo_info=list(Chem.FindPotentialStereo(mol))
    potential={int(s.centeredOn):str(s.specified) for s in stereo_info if str(s.type).startswith('Atom_')}
    potential_bonds={int(s.centeredOn):str(s.specified) for s in stereo_info if str(s.type).startswith('Bond_')}
    atoms=[];x=[];bonds=[];edges=[];attrs=[]
    for a in mol.GetAtoms():
        cip=a.GetProp('_CIPCode') if a.HasProp('_CIPCode') else ''
        stereo=cip if cip else ('UNASSIGNED_POTENTIAL' if potential.get(a.GetIdx())=='Unspecified' else ('OTHER' if a.GetIdx() in potential else 'NONE'))
        values={'element':a.GetSymbol(),'total_degree':a.GetTotalDegree(),'formal_charge':a.GetFormalCharge(),
            'total_H':a.GetTotalNumHs(),'hybridization':str(a.GetHybridization()),'aromatic':a.GetIsAromatic(),
            'in_ring':a.IsInRing(),'CIP_state':stereo,'isotope_specified':a.GetIsotope()!=0}
        x.append(vector('atom',values))
        atoms.append({'atom_index':a.GetIdx(),**values,'raw_CIP':cip,'raw_chiral_tag':str(a.GetChiralTag()),
            'isotope':a.GetIsotope(),'radical_electrons':a.GetNumRadicalElectrons(),
            'implicit_H':a.GetNumImplicitHs(),'explicit_H_count':a.GetNumExplicitHs()})
    for b in mol.GetBonds():
        raw_stereo=str(b.GetStereo())
        feature_stereo='STEREOANY' if potential_bonds.get(b.GetIdx())=='Unspecified' else raw_stereo
        values={'bond_type':str(b.GetBondType()),'stereo':feature_stereo,'conjugated':b.GetIsConjugated(),'in_ring':b.IsInRing()}
        i,j=b.GetBeginAtomIdx(),b.GetEndAtomIdx();attribute=vector('bond',values)
        columns=[len(edges),len(edges)+1];edges.extend([(i,j),(j,i)]);attrs.extend([attribute,attribute.copy()])
        bonds.append({'bond_index':b.GetIdx(),'begin_atom':i,'end_atom':j,**values,'raw_bond_stereo':raw_stereo,
            'potential_stereo_state':potential_bonds.get(b.GetIdx(),''),'raw_bond_direction':str(b.GetBondDir()),
            'stereo_atoms':list(b.GetStereoAtoms()),'forward_column':columns[0],'reverse_column':columns[1]})
    graph=Data(x=torch.tensor(x,dtype=torch.float32).reshape(-1,44),
        edge_index=torch.tensor(edges,dtype=torch.long).reshape(-1,2).T.contiguous(),
        edge_attr=torch.tensor(attrs,dtype=torch.float32).reshape(-1,14),num_nodes=mol.GetNumAtoms())
    validate_graph(graph)
    return graph,{'atoms':atoms,'bonds':bonds}


def validate_graph(data):
    if set(data.keys())!={'x','edge_index','edge_attr','num_nodes'}:raise ValueError('Molecule Data forbids IDs/labels/extra attributes')
    if not isinstance(data.num_nodes,int) or data.num_nodes<1:raise ValueError('Explicit positive num_nodes required')
    if data.edge_index.dtype!=torch.long or data.edge_index.ndim!=2 or data.edge_index.shape[0]!=2:raise ValueError('Integer [2,E] edges')
    if data.x.shape!=(data.num_nodes,44) or data.edge_attr.shape!=(data.edge_index.shape[1],14):raise ValueError('44/14 schema')
    if data.x.dtype not in (torch.float32,torch.float64) or data.edge_attr.dtype!=data.x.dtype:raise ValueError('Float tensor dtype')
    if not torch.isfinite(data.x).all() or not torch.isfinite(data.edge_attr).all():raise ValueError('Nonfinite molecular features')
    for kind,tensor in [('atom',data.x),('bond',data.edge_attr)]:
        for field,section in slices(kind).items():
            block=tensor[:,section]
            if not ((block==0)|(block==1)).all():raise ValueError('Binary/one-hot features required')
            if SCHEMA[kind][field]!=['bool'] and not (block.sum(1)==1).all():raise ValueError('One-hot category missing/ambiguous')
    data.validate(raise_on_error=True)
    e=data.edge_index
    if e.numel() and bool((e[0]==e[1]).any()):raise ValueError('Covalent self-loop')
    index={tuple(pair):i for i,pair in enumerate(e.T.tolist())}
    if len(index)!=e.shape[1]:raise ValueError('Duplicate directed edge')
    for (i,j),column in index.items():
        other=index.get((j,i))
        if other is None or not torch.equal(data.edge_attr[column],data.edge_attr[other]):raise ValueError('Reverse bond feature mismatch')
    return True


def numeric_digest(arrays):
    h=hashlib.sha256()
    for name,value in sorted(arrays.items()):
        a=value.detach().cpu().contiguous().numpy() if torch.is_tensor(value) else np.asarray(value)
        h.update(name.encode());h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()


def graph_arrays(data):
    return {'x':data.x.detach().cpu().numpy(),'edge_index':data.edge_index.detach().cpu().numpy(),
        'edge_attr':data.edge_attr.detach().cpu().numpy(),'num_nodes':np.array(data.num_nodes,dtype=np.int64)}


@lru_cache(maxsize=1)
def approved_atom_ids():
    frame=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv')
    return frozenset(frame[frame.strict_qc_pass].id),frozenset(frame.id)


@dataclass(frozen=True)
class MolecularInput:
    ids:tuple
    batch:Batch
    atom_mask:torch.Tensor


class MolecularStore:
    """Kimlik/yapı metadata'sı ayrı, Data içinde yalnız atom ve bağ alanları."""
    def __init__(self,graphs,registry):
        self.graphs=graphs;self.registry=registry
        approved,all_ids=approved_atom_ids()
        if set(graphs)!=all_ids or set(registry)!=all_ids:raise ValueError('Frozen62 molecular inventory required')
        if {d for d,m in registry.items() if m['atom_eligible']}!=approved:raise ValueError('Frozen54/8 mask mismatch')

    def make_batch(self,ids):
        ids=tuple(ids)
        if not ids or len(set(ids))!=len(ids) or set(ids)-set(self.graphs):raise ValueError('Unique known drug IDs required')
        graphs=[self.graphs[d].clone() for d in ids]
        for data in graphs:validate_graph(data)
        batch=Batch.from_data_list(graphs)
        if batch.edge_index.numel() and not torch.equal(batch.batch[batch.edge_index[0]],batch.batch[batch.edge_index[1]]):raise ValueError('Cross-molecule bond')
        return MolecularInput(ids,batch,torch.tensor([self.registry[d]['atom_eligible'] for d in ids],dtype=torch.bool))


def load_store():
    from wp09_train import sha
    registry=json.loads((QA/'molecule_registry.json').read_text(encoding='utf-8'))
    graphs={}
    for d,meta in registry.items():
        path=ROOT/meta['graph_file']
        if sha(path)!=meta['graph_file_sha256']:raise ValueError('Graph file hash mismatch')
        with np.load(path,allow_pickle=False) as a:
            if set(a.files)!={'x','edge_index','edge_attr','num_nodes'}:raise ValueError('Serialized schema mismatch')
            arrays={k:a[k].copy() for k in a.files}
        if numeric_digest(arrays)!=meta['graph_tensor_sha256']:raise ValueError('Graph numeric hash mismatch')
        graphs[d]=Data(x=torch.from_numpy(arrays['x']),edge_index=torch.from_numpy(arrays['edge_index']),
            edge_attr=torch.from_numpy(arrays['edge_attr']),num_nodes=int(arrays['num_nodes']))
        validate_graph(graphs[d])
    return MolecularStore(graphs,registry)


def prepare(refresh_working_draft=False):
    from wp09_train import sha,write_json
    if (QA/'artifact_validation.json').exists():raise RuntimeError('Encoder v1 finalized; do not overwrite')
    if (QA/'molecule_registry.json').exists() and not refresh_working_draft:raise RuntimeError('Encoder v1 graphs already prepared; do not overwrite')
    source=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv');previous=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv').set_index('id')
    assert len(source)==62 and source.id.is_unique
    folder=QA/'graphs';folder.mkdir(exist_ok=True)
    registry={};rows=[];atom_rows=[];bond_rows=[]
    for row in source.itertuples():
        mol,status=parse_smiles(row.raw_smiles)
        if status!='valid':raise ValueError(f'{row.id}: {status}')
        observed=identity(mol);old=previous.loc[row.id]
        if observed['rdkit_inchikey']!=old.rdkit_inchikey or observed['rdkit_inchikey']!=row.raw_inchikey or row.cid!=old.cid or row.cid!=row.bridge_cid:raise ValueError('Source identity mismatch')
        if (mol.GetNumAtoms(),mol.GetNumBonds(),len(Chem.GetMolFrags(mol)))!=(old.atom_count,old.bond_count,old.components):raise ValueError('Atom/bond/fragment mismatch')
        data,raw=build_graph(mol);path=folder/(row.id+'.npz');arrays=graph_arrays(data);np.savez_compressed(path,**arrays)
        registry[row.id]={'id':row.id,'name':row.name,'cid':int(row.cid),'source_kind':row.source_kind,'source_SMILES':row.raw_smiles,
            'source_SMILES_sha256':hashlib.sha256(row.raw_smiles.encode()).hexdigest(),'source_InChIKey':row.raw_inchikey,
            'atom_eligible':bool(old.strict_qc_pass),'review_flags':'' if pd.isna(old.review_flags) else old.review_flags,
            'graph_file':path.relative_to(ROOT).as_posix(),'graph_file_sha256':sha(path),'graph_tensor_sha256':numeric_digest(arrays),
            'raw_stereo_metadata':raw}
        rows.append({'id':row.id,'name':row.name,'cid':row.cid,'atoms':data.num_nodes,'bonds':mol.GetNumBonds(),'directed_edges':data.num_edges,
            'components':old.components,'atom_eligible':bool(old.strict_qc_pass),'review_flags':registry[row.id]['review_flags'],
            'PyG_validate':True,'identity_match':True,'x_dim':44,'edge_dim':14,'y_present':False,'graph_tensor_sha256':numeric_digest(arrays)})
        atom_rows.extend({'id':row.id,**a} for a in raw['atoms']);bond_rows.extend({'id':row.id,**b} for b in raw['bonds'])
    write_json(QA/'molecule_registry.json',registry)
    for filename,records in [('molecular_graph_QA_all62.csv',rows),('atom_fields_all62.csv',atom_rows),('bond_fields_all62.csv',bond_rows)]:pd.DataFrame(records).to_csv(QA/filename,index=False,encoding='utf-8-sig')
    write_json(QA/'feature_schema.json',{'version':'WP10-44atom-14bond-v1','source_design_sha256':sha(DESIGN),'fields':SCHEMA,
        'atom_columns':schema_columns('atom'),'bond_columns':schema_columns('bond'),'IDs_labels_inside_Data':False,
        'direction_policy':'Both directed edges share invariant bond type/stereo features; raw RDKit BondDir/stereo reference atoms are metadata, not copied as direction-specific features',
        'unknown_stereo_policy':'Unspecified potential atom→UNASSIGNED_POTENTIAL; unspecified potential double bond→STEREOANY; original raw BondStereo unchanged in metadata; no R/S/E/Z inference'})
    paths=['reports/qa/WP04/structure_sources.csv','reports/qa/WP04/structure_validation.csv','configs/WP10_design_PROPOSED_v1.json',
        'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv','reports/qa/WP08/experimental_preparation/frozen_split_manifest.json','scripts/wp09_encoder.py']
    write_json(QA/'input_manifest.json',{p:sha(ROOT/p) for p in paths})
    return load_store()


if __name__=='__main__':
    store=prepare('--refresh-working-draft' in sys.argv);print('Prepared real PyG Data:',len(store.graphs),'atom eligible:',sum(m['atom_eligible'] for m in store.registry.values()))
