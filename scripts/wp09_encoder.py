"""Küçük WP09 encoder: tek gerçek mean-message PPI katmanı; optimizer/eğitim yok."""
import numpy as np
import torch
from torch import nn

ROLES=('target','enzyme','transporter','carrier')
VARIANTS=('G_noPPI','G_realPPI','G_shuffledPPI')


def directed_edges(pairs):
    """Kanonik yönsüz çiftler -> iki yön; self-loop otomatik eklenmez."""
    raw=np.array(pairs,copy=True)
    if not np.issubdtype(raw.dtype,np.integer):raise ValueError('Integer protein indices required')
    pairs=torch.as_tensor(raw,dtype=torch.long)
    if pairs.ndim!=2 or pairs.shape[0]!=2:raise ValueError('Expected canonical pairs shape [2,E]')
    if pairs.numel() and not bool((pairs[0]<pairs[1]).all()):raise ValueError('Canonical unique undirected pairs required')
    if pairs.shape[1]!=len(set(map(tuple,pairs.T.tolist()))):raise ValueError('Duplicate pair')
    return torch.cat([pairs,pairs.flip(0)],dim=1)


class ResidualMeanProtein(nn.Module):
    def __init__(self,inputs=56,hidden=32):
        super().__init__()
        self.projection=nn.Linear(inputs,hidden)
        self.self_update=nn.Linear(hidden,hidden,bias=False)
        self.message=nn.Linear(hidden,hidden,bias=False)

    def forward(self,x,ppi_edge_index):
        if x.ndim!=2 or x.shape[1]!=self.projection.in_features or not torch.isfinite(x).all():raise ValueError('Protein feature schema')
        edges=ppi_edge_index
        if edges.dtype!=torch.long or edges.ndim!=2 or edges.shape[0]!=2:raise ValueError('edge_index shape/dtype')
        if edges.numel() and (int(edges.min())<0 or int(edges.max())>=len(x)):raise ValueError('PPI endpoint index')
        if edges.numel() and bool((edges[0]==edges[1]).any()):raise ValueError('Explicit PPI self-loop forbidden')
        z=torch.relu(self.projection(x))
        source,destination=edges
        total=torch.zeros_like(z).index_add(0,destination,z[source])
        degree=torch.zeros((len(x),1),dtype=z.dtype,device=z.device)
        degree=degree.index_add(0,destination,torch.ones((len(destination),1),dtype=z.dtype,device=z.device))
        neighbor_mean=total/degree.clamp_min(1)
        # Boş komşuluk gerçekten sıfır mesajdır; message katmanında bias yok.
        return z+torch.relu(self.self_update(z)+self.message(neighbor_mean))


class RoleMaskedPPI(nn.Module):
    """Dört ayrı rol mean readout; tüm input eksikse logits NA, önsel fallback yok."""
    def __init__(self,hidden=32,chem_hidden=8,num_targets=None):
        super().__init__()
        self.protein=ResidualMeanProtein(56,hidden)
        self.chemistry=nn.Linear(5,chem_hidden)
        self.hidden=hidden
        self.representation_dim=4*hidden+chem_hidden+5
        self.head=None if num_targets is None else nn.Linear(self.representation_dim,num_targets)

    def encode_proteins(self,protein_x,pairs,variant):
        if variant not in VARIANTS:raise ValueError('Explicit ablation variant required')
        edges=directed_edges(pairs).to(protein_x.device)
        if variant=='G_noPPI':edges=edges[:,:0]
        return self.protein(protein_x,edges)

    def readout(self,protein_h,chemistry,masks,role_edges):
        if chemistry.ndim!=2 or chemistry.shape[1]!=5 or masks.shape!=(len(chemistry),5):raise ValueError('Drug schema')
        if masks.dtype!=torch.bool or set(role_edges)!=set(ROLES):raise ValueError('Four typed roles and boolean masks required')
        if not torch.isfinite(chemistry).all() or not torch.isfinite(protein_h).all():raise ValueError('Nonfinite input')
        if bool((chemistry[~masks[:,0]]!=0).any()):raise ValueError('Absent chemistry must use masked neutral block')
        blocks=[torch.relu(self.chemistry(chemistry))*masks[:,0:1]]
        for j,role in enumerate(ROLES):
            edges=role_edges[role]
            if edges.dtype!=torch.long or edges.ndim!=2 or edges.shape[0]!=2:raise ValueError('Role edge schema')
            if edges.numel() and (int(edges.min())<0 or int(edges[0].max())>=len(chemistry) or int(edges[1].max())>=len(protein_h)):
                raise ValueError('Role endpoint index')
            sums=torch.zeros((len(chemistry),self.hidden),dtype=protein_h.dtype,device=protein_h.device)
            sums=sums.index_add(0,edges[0],protein_h[edges[1]])
            counts=torch.zeros((len(chemistry),1),dtype=protein_h.dtype,device=protein_h.device)
            counts=counts.index_add(0,edges[0],torch.ones((edges.shape[1],1),dtype=protein_h.dtype,device=protein_h.device))
            if not torch.equal(counts[:,0]>0,masks[:,j+1]):raise ValueError('Role mask contradicts typed edges')
            blocks.append((sums/counts.clamp_min(1))*masks[:,j+1:j+2])
        blocks.append(masks.to(chemistry.dtype))
        representation=torch.cat(blocks,dim=1)
        eligible=masks.any(dim=1)
        logits=None if self.head is None else self.head(representation).masked_fill(~eligible[:,None],float('nan'))
        return {'representation':representation,'eligible':eligible,'logits':logits}

    def forward(self,graph,threshold,variant,shuffled_pairs=None):
        if threshold not in (400,700,900):raise ValueError('Explicit reviewed threshold required')
        if variant=='G_shuffledPPI' and shuffled_pairs is None:raise ValueError('Shuffled variant requires explicit null edges')
        if variant!='G_shuffledPPI' and shuffled_pairs is not None:raise ValueError('Null edges only for shuffled variant')
        protein_x=torch.as_tensor(graph['protein_x'],dtype=self.protein.projection.weight.dtype)
        pairs=shuffled_pairs if variant=='G_shuffledPPI' else graph[f'ppi_pairs_{threshold}']
        h=self.encode_proteins(protein_x,pairs,variant)
        output=self.readout(h,torch.as_tensor(graph['chemistry'],dtype=h.dtype),torch.as_tensor(graph['masks'],dtype=torch.bool),
            {role:torch.as_tensor(graph['role_'+role],dtype=torch.long) for role in ROLES})
        return {**output,'protein_h':h}

    def query_readout(self,query,train_protein_h):
        """Cache salt okunur; yeni query proteinleri self-only; query -> train geri mesajı yok."""
        new_x=torch.as_tensor(query['unseen_protein_x'],dtype=train_protein_h.dtype,device=train_protein_h.device)
        empty=torch.empty((2,0),dtype=torch.long,device=train_protein_h.device)
        new_h=self.protein(new_x,empty)
        pool=torch.cat([train_protein_h,new_h],dim=0)
        return self.readout(pool,torch.as_tensor(query['chemistry'],dtype=pool.dtype,device=pool.device),
            torch.as_tensor(query['masks'],dtype=torch.bool,device=pool.device),
            {role:torch.as_tensor(query['role_'+role],dtype=torch.long,device=pool.device) for role in ROLES})


def distinguishing_fixture():
    """56 özellikli gerçek modülde analitik A--B--C ve izole D; rastgele ağırlık yok."""
    encoder=ResidualMeanProtein(56,2).double()
    with torch.no_grad():
        encoder.projection.weight.zero_();encoder.projection.bias.zero_()
        encoder.projection.weight[0,0]=1;encoder.projection.weight[1,1]=1
        encoder.self_update.weight.copy_(torch.eye(2,dtype=torch.float64))
        encoder.message.weight.copy_(torch.eye(2,dtype=torch.float64))
    x=torch.zeros((4,56),dtype=torch.float64);x[:,:2]=torch.tensor([[1,2],[3,1],[2,4],[5,5]],dtype=torch.float64)
    pairs=np.array([[0,1],[1,2]],dtype=np.int64).T
    return encoder,x,pairs
