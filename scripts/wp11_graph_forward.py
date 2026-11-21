"""Salt okunur, sürümlü açıklama forward'ı. Eğitim encoder'ı değişmez."""
from dataclasses import dataclass
import numpy as np
from wp10_molecular_graph import torch,numeric_digest
from wp09_encoder import directed_edges,ROLES


@dataclass(frozen=True)
class ExplanationCache:
    protein_h:torch.Tensor
    source_graph_digest:str
    source_model_digest:str
    intervention:str


def resolve_relation(graph,query,drug_id,role,accession):
    if role not in ROLES:raise ValueError('Unknown role')
    ids=list(query['drug_ids']);pool=list(graph['protein_ids'])+list(query['unseen_protein_ids'])
    if len(set(ids))!=len(ids) or len(set(pool))!=len(pool):raise ValueError('Ambiguous ID alignment')
    if drug_id not in ids or accession not in pool:raise ValueError('Unknown query/protein ID')
    d,p=ids.index(drug_id),pool.index(accession);e=query['role_'+role]
    if int(((e[0]==d)&(e[1]==p)).sum())!=1:raise ValueError('Typed relation absent or duplicate')
    return role,d,p


def pair_index_by_ids(graph,first,second):
    ids=list(graph['protein_ids'])
    if first not in ids or second not in ids or first==second:raise ValueError('Unknown PPI endpoints')
    a,b=sorted([ids.index(first),ids.index(second)]);pairs=graph['ppi_pairs_700']
    ix=np.flatnonzero((pairs[0]==a)&(pairs[1]==b))
    if len(ix)!=1:raise ValueError('Absent/duplicate train PPI edge')
    return int(ix[0])


def protein_messages(encoder,x,pairs,pair_index=None,mode='fixed',ppi_enabled=True):
    if mode not in ('fixed','delete'):raise ValueError('Explicit fixed/delete semantics')
    original=directed_edges(pairs).to(x.device)
    if pair_index is not None and not 0<=pair_index<pairs.shape[1]:raise ValueError('Unknown canonical PPI edge')
    weights=x.new_ones(original.shape[1])
    if pair_index is not None:weights[[pair_index,pair_index+pairs.shape[1]]]=0
    edges=original
    if not ppi_enabled:edges=original[:,:0];weights=weights[:0]
    elif mode=='delete':edges=original[:,weights.bool()];weights=weights[weights.bool()]
    z=torch.relu(encoder.projection(x));src,dst=edges
    total=torch.zeros_like(z).index_add(0,dst,z[src]*weights[:,None])
    # Fixed masks retain ORIGINAL degree;physical deletion recomputes it.
    degree=torch.zeros((len(z),1),dtype=z.dtype,device=z.device).index_add(0,dst,torch.ones((len(dst),1),dtype=z.dtype,device=z.device))
    mean=total/degree.clamp_min(1);h=z+torch.relu(encoder.self_update(z)+encoder.message(mean))
    return {'h':h,'mean':mean,'degree':degree,'directed_edges':edges,'weights':weights}


def typed_readout(base,pool,query,relation=None,mode='fixed'):
    """relation=(role,drug_index,protein_index); masks/denominators separately handled."""
    if mode not in ('fixed','delete'):raise ValueError('Explicit role semantics')
    masks=torch.as_tensor(query['masks'].copy(),dtype=torch.bool,device=pool.device)
    chemistry=torch.as_tensor(query['chemistry'],dtype=pool.dtype,device=pool.device)
    if relation is not None:
        role,drug,protein=relation
        if role not in ROLES:raise ValueError('Unknown typed role')
        e=query['role_'+role]
        if int(((e[0]==drug)&(e[1]==protein)).sum())!=1:raise ValueError('Absent/duplicate typed relation is NA,not zero')
    blocks=[torch.relu(base.chemistry(chemistry))*masks[:,0:1]]
    for j,role in enumerate(ROLES):
        e=torch.as_tensor(query['role_'+role],dtype=torch.long,device=pool.device);weights=pool.new_ones(e.shape[1])
        if relation is not None and relation[0]==role:weights[(e[0]==relation[1])&(e[1]==relation[2])]=0
        if mode=='delete':e=e[:,weights.bool()];weights=weights[weights.bool()]
        total=torch.zeros((len(chemistry),base.hidden),dtype=pool.dtype,device=pool.device).index_add(0,e[0],pool[e[1]]*weights[:,None])
        count=torch.zeros((len(chemistry),1),dtype=pool.dtype,device=pool.device).index_add(0,e[0],torch.ones((e.shape[1],1),dtype=pool.dtype,device=pool.device))
        if mode=='delete':masks[:,j+1]=count[:,0]>0
        blocks.append(total/count.clamp_min(1)*masks[:,j+1:j+2])
    blocks.append(masks.to(pool.dtype));representation=torch.cat(blocks,1)
    return {'representation':representation,'eligible':masks.any(1),'masks':masks}


def query_logits(model,query,cache,unseen_h,atom_block,atom_mask,source_graph_digest,relation=None,mode='fixed'):
    if not isinstance(cache,ExplanationCache) or cache.source_graph_digest!=source_graph_digest or cache.source_model_digest!=numeric_digest(model.state_dict()):raise ValueError('Cache source/model identity mismatch')
    pool=torch.cat([cache.protein_h,unseen_h],0)
    base=typed_readout(model.base,pool,query,relation,mode)
    representation=torch.cat([base['representation'],atom_block,atom_mask[:,None].to(pool.dtype)],1)
    logits=model.head(representation).masked_fill(~base['eligible'][:,None],float('nan'))
    return {'logits':logits,'representation':representation,'eligible':base['eligible'],'pool':pool}


def cache_for(model,graph,pair_index=None,mode='fixed'):
    dtype=model.base.protein.projection.weight.dtype
    x=torch.as_tensor(graph['protein_x'],dtype=dtype)
    out=protein_messages(model.base.protein,x,graph['ppi_pairs_700'],pair_index,mode)
    # A dedicated mask identity;does not spoof the accepted ProteinCache contract.
    key='none' if pair_index is None else mode+':'+str(pair_index)
    return ExplanationCache(out['h'],numeric_digest(graph),numeric_digest(model.state_dict()),key)
