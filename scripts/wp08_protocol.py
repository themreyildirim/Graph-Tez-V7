"""WP08 metodoloji sınırları: yalnız yardımcı kontroller, sınıflandırıcı yok.

Gerçek kohortta fit/split yapılmaz. Testler sentetik veriyle fit sınırını sınar.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def check_partition(train_ids,val_ids,test_ids,universe,groups):
    parts=[list(train_ids),list(val_ids),list(test_ids)]
    if any(not p or len(p)!=len(set(p)) for p in parts):raise ValueError('Empty/duplicate partition')
    sets=list(map(set,parts));values=list(universe);whole=set(values)
    if len(whole)!=len(values):raise ValueError('Duplicate cohort ID')
    if any(sets[i]&sets[j] for i in range(3) for j in range(i+1,3)):raise ValueError('Drug overlap')
    if set.union(*sets)!=whole:raise ValueError('Missing/unknown cohort ID')
    if set(groups)!=whole:raise ValueError('Group identity coverage')
    grouped=[{groups[d] for d in s} for s in sets]
    if any(grouped[i]&grouped[j] for i in range(3) for j in range(i+1,3)):raise ValueError('Structure group leakage')
    return True


def training_vocabulary(positives,train_ids,groups,min_drugs,min_groups):
    """Eşik kullanıcıca önceden onaylanmalı; heldout desteği karar hesabına girmez."""
    if min_drugs<1 or min_groups<1:raise ValueError('Invalid support threshold')
    if not {'drug_id','pt_cui'}<=set(positives.columns):raise ValueError('Positive schema')
    ids=set(train_ids)
    if not ids or not ids<=set(groups):raise ValueError('Training/group IDs')
    local=positives[positives.drug_id.isin(ids)][['drug_id','pt_cui']].copy()
    if local.duplicated(['drug_id','pt_cui']).any():raise ValueError('Duplicate training positive pair')
    local['group']=local.drug_id.map(groups)
    support=local.groupby('pt_cui').agg(train_drugs=('drug_id','nunique'),train_groups=('group','nunique'))
    return sorted(support[(support.train_drugs>=min_drugs)&(support.train_groups>=min_groups)].index)


class GuardedPreprocessor:
    """Train kimliği zorunlu median+standardizasyon örneği; onaylanmış politika değil.

    Maskeli dal birincil adaydır. Bu imputasyon seçeneği yalnız sentetik testte
    uygulanır; boş sütun uydurulmaz. Kimlik/provenans kolonları sayıya çevrilmez.
    """
    def __init__(self,columns):
        self.columns=list(columns);self.fitted=False

    def fit(self,features,train_ids):
        ids=list(train_ids)
        if not ids or len(ids)!=len(set(ids)) or features.index.duplicated().any():raise ValueError('Invalid training IDs')
        if set(features.index)!=set(ids):raise ValueError('Fit frame must contain exactly training IDs')
        if list(features.columns)!=self.columns:raise ValueError('Feature allowlist/order')
        data=features.astype(float)
        if np.isinf(data.to_numpy()).any():raise ValueError('Infinite feature')
        if data.isna().all().any():raise ValueError('Entire column unknown in training; policy required')
        self.median=data.median();filled=data.fillna(self.median)
        self.mean=filled.mean();self.std=filled.std(ddof=0).replace(0,1)
        self.fit_ids=tuple(sorted(ids));self.fitted=True
        return self

    def transform(self,features):
        if not self.fitted:raise RuntimeError('Fit first')
        if list(features.columns)!=self.columns or features.index.duplicated().any():raise ValueError('Transform schema')
        data=features.astype(float)
        if np.isinf(data.to_numpy()).any():raise ValueError('Infinite feature')
        return (data.fillna(self.median)-self.mean)/self.std


def new_partition_graph(drug_ids,typed_edges,protein_registry,train_ids,heldout_ids,
                        protein_policy,ppi_pairs=(),strict_human_accessions=()):
    """Onaylı split SONRASI kullanılacak üretici; WP07 .pt okumaz, x/y oluşturmaz.

    Burada sadece sentetik/gerçek sınır testinde çağrılır; final split veya graf
    dosyası üretilmez. PPI encoder/forward veya öğrenme yapılmaz.
    """
    sys.path.insert(0,str(ROOT/'.deps/pyg'))
    import torch
    from torch_geometric.data import HeteroData
    roles=('target','enzyme','transporter','carrier')
    ids=set(drug_ids);train=set(train_ids);heldout=set(heldout_ids)
    if not train or train&heldout or train|heldout!=ids:raise ValueError('Train/heldout boundary')
    if set(typed_edges.role)-set(roles):raise ValueError('Unapproved relation')
    if typed_edges.duplicated(['drug_id','accession','role']).any():raise ValueError('Duplicate relation')
    if not set(typed_edges.drug_id)<=ids:raise ValueError('Unknown drug edge')
    registered=set(protein_registry.accession)
    if len(registered)!=len(protein_registry) or not set(typed_edges.accession)<=registered:raise ValueError('Protein identity')
    local=typed_edges[typed_edges.drug_id.isin(train)]
    if protein_policy=='train_linked_only':proteins=sorted(set(local.accession))
    elif protein_policy=='fixed_registry_review':proteins=sorted(registered)
    else:raise ValueError('Explicit protein universe policy required')
    graph=HeteroData();graph.purpose='WP08_boundary_test_only';graph.training_ready=False
    graph['drug'].canonical_ids=sorted(train);graph['drug'].num_nodes=len(train)
    graph['protein'].canonical_ids=proteins;graph['protein'].num_nodes=len(proteins)
    di={d:i for i,d in enumerate(sorted(train))};pi={p:i for i,p in enumerate(proteins)}
    for role in roles:
        selected=local[local.role.eq(role)]
        rows=[[di[r.drug_id],pi[r.accession]] for r in selected.itertuples()]
        graph['drug',role,'protein'].edge_index=torch.tensor(rows,dtype=torch.long).t().contiguous() if rows else torch.empty((2,0),dtype=torch.long)
    ppi=list(ppi_pairs);strict=set(strict_human_accessions)
    if ppi:
        if 'taxid' not in protein_registry:raise ValueError('Taxonomy evidence required for PPI')
        source_human=set(protein_registry[protein_registry.taxid.astype(str).eq('9606')].accession)
        if not strict<=source_human:raise ValueError('Caller scope contradicts source taxonomy')
    if len(ppi)!=len(set(ppi)):raise ValueError('Duplicate PPI pair')
    if any(a==b or a not in strict or b not in strict for a,b in ppi):raise ValueError('Nonhuman/review/context PPI')
    selected=[(a,b) for a,b in ppi if a in pi and b in pi]
    if selected:
        both=selected+[(b,a) for a,b in selected]
        if len(both)!=len(set(both)):raise ValueError('PPI canonical pair duplication')
        graph['protein','ppi_human','protein'].edge_index=torch.tensor([[pi[a],pi[b]] for a,b in both],dtype=torch.long).t().contiguous()
    graph.validate(raise_on_error=True)
    validate_partition_graph(graph,train,heldout)
    return graph


def validate_partition_graph(graph,train_ids,heldout_ids):
    train=set(train_ids);heldout=set(heldout_ids)
    if train&heldout or set(graph['drug'].canonical_ids)!=train:raise ValueError('Drug graph leakage')
    if set(graph.node_types)!={'drug','protein'}:raise ValueError('Target node leakage')
    roles={'target','enzyme','transporter','carrier'}
    for t in graph.node_types:
        if set(graph[t].keys())!={'canonical_ids','num_nodes'}:raise ValueError('Feature/label leakage')
    for src,rel,dst in graph.edge_types:
        if not (src=='drug' and dst=='protein' and rel in roles or src==dst=='protein' and rel=='ppi_human'):
            raise ValueError('Reverse/target/unknown relation forbidden')
        if set(graph[src,rel,dst].keys())!={'edge_index'}:raise ValueError('Unapproved edge attribute')
    graph.validate(raise_on_error=True)
    return True


def training_gate(configuration):
    if configuration.get('status')!='APPROVED_BY_USER':raise RuntimeError('Protocol approval pending; no training')
    raise RuntimeError('WP08 protocol module contains no trainer; separate explicit training task required')
