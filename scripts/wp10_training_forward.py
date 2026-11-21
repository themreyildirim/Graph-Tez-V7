"""Bir kez doğrulanmış sabit girdilerde kabul edilen encoder'ın aynı hesabı.

Her epoch'ta PyG Data listesini yeniden ayrıştırmaz; ağırlıklar ve mesaj denklemi
aynıdır. Eşitlik ve gradient testleri referans encode_train/query ile karşılaştırır.
"""
from dataclasses import dataclass
import copy
from wp10_molecular_graph import torch,numeric_digest
from wp10_molecular_encoder import validate_batch
from wp09_encoder import directed_edges,ROLES
from torch_geometric.nn import global_mean_pool


@dataclass(frozen=True)
class Prepared:
    graph:dict
    molecules:object
    digest:str


def prepare(model,graph,molecules):
    model._check_molecules(molecules,graph['drug_ids'])
    frozen=copy.deepcopy(graph);mol=copy.deepcopy(molecules)
    return Prepared(frozen,mol,input_digest(frozen,mol))


def input_digest(graph,molecules):
    return numeric_digest({**graph,'molecule_x':molecules.batch.x,'molecule_edges':molecules.batch.edge_index,
        'molecule_attr':molecules.batch.edge_attr,'molecule_batch':molecules.batch.batch,'atom_mask':molecules.atom_mask})


def molecular_forward(model,batch):
    m=model.molecular;x=batch.x;edges=batch.edge_index;src,dst=edges
    h0=torch.relu(m.projection(x))
    messages=torch.relu(m.atom_message(h0[src])+m.bond_message(batch.edge_attr))
    sums=torch.zeros_like(h0).index_add(0,dst,messages)
    counts=torch.zeros((len(h0),1),dtype=x.dtype).index_add(0,dst,torch.ones((len(dst),1),dtype=x.dtype))
    h=h0+torch.relu(m.self_update(h0)+sums/counts.clamp_min(1))
    return torch.relu(m.readout(global_mean_pool(h,batch.batch,size=batch.num_graphs)))


def fuse(model,base,prepared,variant):
    mask=prepared.molecules.atom_mask & (variant[1]=='1')
    block=molecular_forward(model,prepared.molecules.batch)*mask[:,None] if variant[1]=='1' else base['representation'].new_zeros((len(mask),8))
    representation=torch.cat([base['representation'],block,mask[:,None].to(block.dtype)],dim=1)
    logits=model.head(representation).masked_fill(~base['eligible'][:,None],float('nan'))
    return {'logits':logits,'representation':representation,'eligible':base['eligible']}


def train_forward(model,prepared,variant):
    g=prepared.graph
    base=model.base.forward(g,700,'G_realPPI' if variant[-1]=='1' else 'G_noPPI')
    return {**fuse(model,base,prepared,variant),'protein_h':base['protein_h']}


def query_forward(model,prepared,train_h,variant):
    base=model.base.query_readout(prepared.graph,train_h)
    return fuse(model,base,prepared,variant)
