"""Tek bond-aware residual mean katmanı ve WP09 ile 150-boyutlu füzyon."""
from dataclasses import dataclass
import numpy as np
from wp10_molecular_graph import (ROOT,QA,Data,Batch,torch,validate_graph,approved_atom_ids,
    MolecularInput,numeric_digest)
from torch import nn
from torch_geometric.nn import global_mean_pool
from wp09_encoder import RoleMaskedPPI
from wp09_data import validate_bundle

VARIANTS=('A0P0','A0P1','A1P0','A1P1')


def model_digest(model):return numeric_digest(model.state_dict())


def validate_batch(batch):
    if not isinstance(batch,Batch):raise ValueError('PyG Batch required')
    if set(batch.keys())!={'x','edge_index','edge_attr','num_nodes','batch','ptr'}:raise ValueError('Batch forbids IDs/targets/extra fields')
    if batch.batch.dtype!=torch.long or batch.ptr.dtype!=torch.long:raise ValueError('Batch integer indices')
    for data in batch.to_data_list():validate_graph(data)
    e=batch.edge_index
    if e.numel() and not torch.equal(batch.batch[e[0]],batch.batch[e[1]]):raise ValueError('Cross-molecule edge')
    return True


class BondAwareMolecularEncoder(nn.Module):
    """44→16;h1=h0+relu(S h0+mean relu(U h0_j+V e_ji));mean→8."""
    def __init__(self):
        super().__init__()
        self.projection=nn.Linear(44,16)
        self.self_update=nn.Linear(16,16,bias=False)
        self.atom_message=nn.Linear(16,16,bias=False)
        self.bond_message=nn.Linear(14,16,bias=False)
        self.readout=nn.Linear(16,8)

    def forward(self,batch):
        validate_batch(batch)
        x=batch.x.to(dtype=self.projection.weight.dtype,device=self.projection.weight.device)
        edge_attr=batch.edge_attr.to(dtype=x.dtype,device=x.device);edges=batch.edge_index.to(x.device)
        h0=torch.relu(self.projection(x));src,dst=edges
        messages=torch.relu(self.atom_message(h0[src])+self.bond_message(edge_attr))
        sums=torch.zeros_like(h0).index_add(0,dst,messages)
        counts=torch.zeros((len(h0),1),dtype=x.dtype,device=x.device).index_add(0,dst,torch.ones((len(dst),1),dtype=x.dtype,device=x.device))
        mean=sums/counts.clamp_min(1)
        h=h0+torch.relu(self.self_update(h0)+mean)
        pooled=global_mean_pool(h,batch.batch.to(x.device),size=batch.num_graphs)
        output=torch.relu(self.readout(pooled))
        return {'molecular_h':output,'node_h':h,'node_h0':h0,'neighbor_mean':mean}


@dataclass(frozen=True)
class ProteinCache:
    protein_h:torch.Tensor
    graph_digest:str
    model_digest:str
    variant:str


class MolecularProteinFusion(nn.Module):
    """Head varsayılan yok: gerçek veride yalnız temsil,PT skoru veya loss yok."""
    def __init__(self,num_targets=None):
        super().__init__()
        self.base=RoleMaskedPPI(num_targets=None)  # WP09 modülü aynen;eski ağırlıklar yüklenmez.
        self.molecular=BondAwareMolecularEncoder()
        self.head=None if num_targets is None else nn.Linear(150,num_targets)
        self.representation_dim=150

    def _check_molecules(self,molecules,ids):
        if not isinstance(molecules,MolecularInput) or molecules.ids!=tuple(ids):raise ValueError('Ordered molecular IDs must equal requested train/query IDs')
        approved,all_ids=approved_atom_ids()
        expected=torch.tensor([d in approved for d in ids],dtype=torch.bool,device=molecules.atom_mask.device)
        if set(ids)-all_ids or molecules.atom_mask.dtype!=torch.bool or not torch.equal(expected,molecules.atom_mask):raise ValueError('Frozen QC54/8 masks required')
        if molecules.batch.num_graphs!=len(ids):raise ValueError('One molecular graph per drug')
        validate_batch(molecules.batch)

    def _fuse(self,base,molecules,variant):
        if variant not in VARIANTS:raise ValueError('Explicit A0P0/A0P1/A1P0/A1P1 required')
        if self.base.head is not None:raise ValueError('WP09 PT head must not enter feature backbone')
        mask=molecules.atom_mask.to(base['representation'].device)&(variant[1]=='1')
        if bool((mask&~base['eligible']).any()):raise ValueError('Atom branch cannot expand frozen61 eligibility')
        if variant[1]=='1':raw=self.molecular(molecules.batch)['molecular_h'];block=raw*mask[:,None]
        else:block=base['representation'].new_zeros((len(mask),8))
        representation=torch.cat([base['representation'],block,mask[:,None].to(block.dtype)],dim=1)
        if representation.shape[1]!=150:raise ValueError('150-dimensional fusion required')
        logits=None if self.head is None else self.head(representation).masked_fill(~base['eligible'][:,None],float('nan'))
        return {'representation':representation,'base_representation':base['representation'],'molecular_block':block,
            'effective_atom_mask':mask,'eligible':base['eligible'],'logits':logits}

    def encode_train(self,graph,molecules,variant):
        validate_bundle(graph);self._check_molecules(molecules,graph['drug_ids'])
        if variant not in VARIANTS:raise ValueError('Unknown ablation')
        base=self.base.forward(graph,700,'G_realPPI' if variant[-1]=='1' else 'G_noPPI')
        output=self._fuse(base,molecules,variant)
        cache=ProteinCache(base['protein_h'],numeric_digest(graph),model_digest(self),variant)
        return {**output,'cache':cache}

    def encode_query(self,graph,query,molecules,cache):
        validate_bundle(graph,query);self._check_molecules(molecules,query['drug_ids'])
        if not isinstance(cache,ProteinCache) or cache.graph_digest!=numeric_digest(graph) or cache.model_digest!=model_digest(self):raise ValueError('Cache belongs to different graph/model state')
        if cache.protein_h.shape!=(len(graph['protein_ids']),32):raise ValueError('Train cache shape')
        base=self.base.query_readout(query,cache.protein_h)
        return self._fuse(base,molecules,cache.variant)


def initialized_model(seed=20261106,num_targets=None,dtype=torch.float32):
    # Tekrar üretilebilir başlangıç; çağıranın RNG durumuna dokunmaz.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed));model=MolecularProteinFusion(num_targets).to(dtype=dtype)
    return model


def validate_context_bundles(context,graph,query):
    """Genel encoder'dan ayrı: belirli fold için doğrulanmış train/query sınırı."""
    import pandas as pd
    partitions=pd.read_csv(ROOT/'reports/qa/WP08/experimental_preparation/nested_partitions_v1.csv')
    local=partitions[partitions.context.eq(context)]
    if local.empty:raise ValueError('Unknown frozen context')
    validate_bundle(graph,query)
    if set(graph['drug_ids'])!=set(local[local.split.eq('train')].drug_id):raise ValueError('Train drug identity mismatch')
    if set(query['drug_ids'])!=set(local[~local.split.eq('train')].drug_id):raise ValueError('Query identity mismatch')
    for split in ('validation','test'):
        if set(query['drug_ids'][query['split']==split])!=set(local[local.split.eq(split)].drug_id):raise ValueError('Query split mismatch')
    return True


def load_context(context,store):
    """Train/query sınırları frozen WP08 üyelikleriyle eşleşir;etiket okunmaz."""
    bundles=[]
    for kind in ('train','query'):
        with np.load(ROOT/f'reports/qa/WP09/design_v1/folds/{context}_{kind}.npz',allow_pickle=False) as a:bundles.append({k:a[k].copy() for k in a.files})
    graph,query=bundles;validate_context_bundles(context,graph,query)
    return graph,query,store.make_batch(graph['drug_ids']),store.make_batch(query['drug_ids'])
