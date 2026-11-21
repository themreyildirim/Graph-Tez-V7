"""Ayrı kenar-sırası ve gerçek Δz kararlılığı; yöntem/seed seçimi yapmaz."""
import copy,json
import numpy as np
import pandas as pd
from wp11_graph_policy import ROOT,QA,ROLES,preserve
from wp11_graph_run import load,forward,old
from wp11_graph_forward import cache_for,pair_index_by_ids,resolve_relation,torch


def run():
    path=QA/'additional_delta_stability.csv'
    if path.exists():raise RuntimeError('Additional QA already exists')
    torch.set_num_threads(1);rows=[]
    with torch.no_grad():
        for c in json.loads((QA/'frozen_contexts.json').read_text()):
            s=load(c['context']);g,q=s['g'],s['q'];base=forward(s)['logits'];m=s['model']
            gp=copy.deepcopy(g);qp=copy.deepcopy(q)
            for threshold in [400,700,900]:gp[f'ppi_pairs_{threshold}']=gp[f'ppi_pairs_{threshold}'][:,::-1].copy()
            for role in ROLES:gp['role_'+role]=gp['role_'+role][:,::-1].copy();qp['role_'+role]=qp['role_'+role][:,::-1].copy()
            sp={**s,'g':gp,'q':qp,'cache':cache_for(m,gp)};basep=forward(sp)['logits']
            a,b=g['protein_ids'][g['ppi_pairs_700'][:,0]];ei=pair_index_by_ids(gp,a,b)
            delta=base-forward(s,cache=cache_for(m,g,0))['logits'];deltap=basep-forward(sp,cache=cache_for(m,gp,ei))['logits']
            rows.append({'context':c['context'],'check':'edge_order_PPI_delta_z','max_abs_error':float(torch.nan_to_num(delta-deltap).abs().max())})
            role,d,p=next((role,int(d),int(p)) for role in ROLES for d,p in q['role_'+role].T)
            delta=base-forward(s,relation=(role,d,p))['logits'];deltap=basep-forward(sp,relation=(role,d,p))['logits']
            rows.append({'context':c['context'],'check':'edge_order_role_delta_z','max_abs_error':float(torch.nan_to_num(delta-deltap).abs().max())})
            drug=q['drug_ids'][d];acc=(list(g['protein_ids'])+list(q['unseen_protein_ids']))[p];one=old.select_query(q,[drug],len(g['protein_ids']))
            so={**s,'q':one,'unseen':m.base.protein(torch.tensor(one['unseen_protein_x'],dtype=torch.float32),torch.empty((2,0),dtype=torch.long)),'atom_block':s['atom_block'][d:d+1],'atom_mask':s['atom_mask'][d:d+1]}
            rel=resolve_relation(g,one,drug,role,acc);do=forward(so)['logits'][0]-forward(so,relation=rel)['logits'][0]
            rows.append({'context':c['context'],'check':'query_alone_role_delta_z','max_abs_error':float(torch.nan_to_num(delta[d]-do).abs().max())})
    assert max(r['max_abs_error'] for r in rows)<=1e-5;preserve();pd.DataFrame(rows).to_csv(path,index=False,encoding='utf-8-sig')
    print(pd.DataFrame(rows).groupby('check').max_abs_error.max().to_string())


if __name__=='__main__':run()
