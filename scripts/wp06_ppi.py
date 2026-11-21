"""STRING links akışları, yönsüz tekilleştirme, eşikler ve sınırlı bağlam ağı."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,hashlib,time,os
import pandas as pd
import networkx as nx
import psutil
from wp06_mapping import ROOT,QA,DEFAULT,NETWORK_DIR,source_path

THRESHOLDS=(150,400,700,900)
NEIGHBOR_MIN_SCORE=700;NEIGHBORS_PER_SEED=3;CONTEXT_BUDGET=40


def valid_link(a,b,score,taxid):
    if not a.startswith(taxid+'.') or not b.startswith(taxid+'.'):return 'taxon_prefix_mismatch'
    try:value=int(score)
    except (ValueError,TypeError):return 'noninteger_score'
    if not 0<=value<=1000:return 'score_out_of_range'
    if a==b:return 'self_loop'
    return 'valid'


class EdgeStore:
    def __init__(self):self.data={}
    def add(self,a,b,score,line):
        if a==b:return
        pair=tuple(sorted((a,b)));direction=0 if a==pair[0] else 1
        if pair not in self.data:self.data[pair]={'protein1':pair[0],'protein2':pair[1],'score_min':score,'score_max':score,'counts':[0,0],'source_lines':[]}
        d=self.data[pair];d['score_min']=min(d['score_min'],score);d['score_max']=max(d['score_max'],score)
        d['counts'][direction]+=1;d['source_lines'].append(line)
    def rows(self,taxid):
        return [{k:d[k] for k in ['protein1','protein2']}|{'network_taxid':taxid,'combined_score':d['score_max'],
            'score_conflict':d['score_min']!=d['score_max'],'source_rows':sum(d['counts']),
            'same_direction_duplicate_excess':sum(max(0,n-1) for n in d['counts']),
            'reciprocal_pair_observed':all(d['counts']),'source_lines':'|'.join(map(str,d['source_lines']))}
            for _,d in sorted(self.data.items())]


def scan_links(path,taxid,seeds,selected=None,full_statistics=True):
    before=path.stat();start=time.monotonic();sha=hashlib.sha256();stats=Counter();hist=Counter();store=EdgeStore()
    candidates={s:{} for s in seeds};nodes=set();examples=[];minimum=1001;maximum=-1
    with path.open('rb') as f:
        head=f.readline();sha.update(head)
        if head.decode().split()!=['protein1','protein2','combined_score']:raise ValueError('Unexpected links schema')
        for line_no,line in enumerate(f,2):
            if full_statistics:sha.update(line)
            stats['rows']+=1
            parts=line.split()
            if len(parts)!=3:stats['malformed_rows']+=1;continue
            a,b=parts[0].decode(),parts[1].decode()
            status=valid_link(a,b,parts[2],taxid)
            if status!='valid':stats[status]+=1;continue
            score=int(parts[2])
            if full_statistics:
                hist[score]+=1;minimum=min(minimum,score);maximum=max(maximum,score)
                nodes.add(a);nodes.add(b);stats['orientation_AB' if a<b else 'orientation_BA']+=1
                if len(examples)<3:examples.append([a,b,score])
            if selected is not None:
                if a in selected and b in selected:store.add(a,b,score,line_no)
            else:
                if a in seeds and b in seeds:store.add(a,b,score,line_no)
                if score>=NEIGHBOR_MIN_SCORE:
                    for seed,neighbor in [(a,b),(b,a)]:
                        if seed in seeds and neighbor not in seeds:
                            top=candidates[seed];top[neighbor]=max(top.get(neighbor,0),score)
                            if len(top)>NEIGHBORS_PER_SEED:
                                worst=max(top,key=lambda n:(-top[n],n));del top[worst]
            if stats['rows']%3000000==0:print(taxid,'links rows',stats['rows'],'second pass' if selected is not None else 'first pass',flush=True)
    after=path.stat();mem=psutil.Process().memory_info()
    meta={'file':str(path),'taxid':taxid,'kind':'links','version':'12.0 filename','size_bytes':before.st_size,
        'mtime_ns':before.st_mtime_ns,'columns':['protein1','protein2','combined_score'],'statistics_scope':'whole_file_rows' if full_statistics else 'expanded_induced_second_pass',
        **stats,'elapsed_seconds':time.monotonic()-start,'os_peak_wset_mib':getattr(mem,'peak_wset',mem.rss)/2**20,
        'metadata_unchanged':before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns}
    if full_statistics:meta.update(sha256=sha.hexdigest(),score_min=minimum,score_max=maximum,unique_source_nodes=len(nodes),examples=examples)
    return store.rows(taxid),candidates,meta,hist


def network_metrics(nodes,edges,threshold):
    graph=nx.Graph();graph.add_nodes_from(nodes)
    for r in edges:
        if r['protein1'] not in nodes or r['protein2'] not in nodes:raise ValueError('Edge endpoint outside declared graph nodes')
        if r['protein1'].split('.',1)[0]!=r['protein2'].split('.',1)[0]:raise ValueError('Cross-organism PPI is forbidden')
        if not r['score_conflict'] and int(r['combined_score'])>=threshold:
            graph.add_edge(r['protein1'],r['protein2'],weight=int(r['combined_score'])/1000)
    comps=list(nx.connected_components(graph));degrees=dict(graph.degree())
    result={'threshold':threshold,'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),
        'nonisolated_nodes':sum(x>0 for x in degrees.values()),'isolates':sum(x==0 for x in degrees.values()),
        'components':len(comps),'largest_component':max(map(len,comps),default=0),
        'density':nx.density(graph),'mean_degree':sum(degrees.values())/len(nodes) if nodes else 0,
        'mean_weighted_strength':sum(dict(graph.degree(weight='weight')).values())/len(nodes) if nodes else 0}
    return result,graph


def component_layout(graph):
    """Bileşenleri ayrı yerleştir: izoleler ana bileşeni okunmaz biçimde sıkıştırmasın."""
    import math
    parts=sorted(nx.connected_components(graph),key=lambda c:(-len(c),sorted(c)))
    positions={};other_rows=max(1,math.ceil(max(0,len(parts)-1)/2))
    for i,part in enumerate(parts):
        ordered=nx.Graph();ordered.add_nodes_from(sorted(part));ordered.add_edges_from(sorted(graph.subgraph(part).edges()))
        local=nx.spring_layout(ordered,seed=42,weight=None,iterations=200,scale=1 if i==0 else .17)
        cx=0 if i==0 else 2.0+((i-1)%2)*.65
        cy=0 if i==0 else 1-2*((i-1)//2)/max(1,other_rows-1)
        for n,xy in local.items():positions[n]=(float(xy[0])+cx,float(xy[1])+cy)
    return positions


def annotate_context(path,taxid,nodes):
    """Yalnız aliases isim/kimlik kanıtı; context düğümü DrugBank hedefi yapılmaz."""
    choices={};evidence=[]
    priorities={'Ensembl_HGNC_name':0,'UniProt_DE_RecName_Full':0,'Ensembl_Description':1,'UniProt_Recommended_Name':1,
        'UniProt_Protein_Name':1,'RefSeq_product':1,'Ensembl_HGNC_symbol':2,'UniProt_GN':2,'UniProt_GN_Name':2,'Ensembl_gene':3}
    with path.open('rb') as f:
        f.readline()
        for no,line in enumerate(f,2):
            parts=line.rstrip(b'\r\n').split(b'\t',2)
            if len(parts)!=3:continue
            sid=parts[0].decode()
            if sid not in nodes:continue
            alias,src=parts[1].decode(),parts[2].decode();tokens=src.split()
            rank=min([priorities[t] for t in tokens if t in priorities]+[99])
            if rank<99:
                evidence.append({'string_id':sid,'alias':alias,'alias_source':src,'source_line':no,'network_taxid':taxid})
                candidate=(rank,alias,src,no)
                if sid not in choices or candidate<choices[sid]:choices[sid]=candidate
    return choices,evidence


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset-root',type=Path,default=Path(os.environ.get('GRAPH_TEZ_DATA_ROOT',str(DEFAULT))))
    parser.add_argument('--annotate-only',action='store_true');args=parser.parse_args()
    if args.annotate_only:
        nodes=pd.read_csv(QA/'ppi_nodes.csv',dtype={'network_taxid':str},keep_default_na=False);annotations=[]
        for tax in NETWORK_DIR:
            ids=set(nodes[nodes.network_taxid.eq(tax)&nodes.node_role.eq('STRING_context_only')].string_id)
            names,ev=annotate_context(source_path(args.dataset_root,tax,'aliases'),tax,ids);annotations+=ev
            for i,r in nodes.iterrows():
                if r.string_id in names:
                    nodes.loc[i,'display_alias']=names[r.string_id][1]
                    nodes.loc[i,'display_name_source']=names[r.string_id][2]
        nodes.to_csv(QA/'ppi_nodes.csv',index=False,encoding='utf-8-sig')
        pd.DataFrame(annotations).to_csv(QA/'context_alias_evidence.csv',index=False,encoding='utf-8-sig')
        print('Refreshed only context names from aliases; links not scanned');return
    mapping=pd.read_csv(QA/'protein_string_mapping.csv',dtype={'network_taxid':str},keep_default_na=False)
    all_edges=[];expanded=[];node_rows=[];metrics=[];manifests=[];score_rows=[];selection=[];context_aliases=[]
    for tax in NETWORK_DIR:
        chosen=mapping[mapping.network_taxid.eq(tax)&mapping.alias_identity_unique]
        seeds=set(chosen.string_id);scope='exact_taxon' if tax=='9606' else 'K12_parent_scope_review'
        # 23 E. coli bağlamı ayrı keşif senaryosu: strict-taxon ağa otomatik eklenmez.
        rows,candidates,meta,hist=scan_links(source_path(args.dataset_root,tax,'links'),tax,seeds)
        manifests.append(meta);all_edges +=[{**r,'mapping_scope':scope} for r in rows]
        score_rows +=[{'network_taxid':tax,'combined_score':k,'raw_rows':v} for k,v in sorted(hist.items())]
        scored={}
        for s,top in candidates.items():
            for n,score in top.items():scored[n]=max(scored.get(n,0),score)
        context=sorted(scored,key=lambda n:(-scored[n],n))[:CONTEXT_BUDGET];selected=seeds|set(context)
        for n in context:selection.append({'string_id':n,'network_taxid':tax,'selection_score':scored[n],
            'evidence_seed_STRING_ids':'|'.join(sorted(s for s,top in candidates.items() if n in top)),
            'policy':'top3 per seed at >=700, score descending then ID, at most40 per organism','drugbank_target':False})
        ext,_,second,_=scan_links(source_path(args.dataset_root,tax,'links'),tax,seeds,selected,False)
        manifests.append(second);expanded +=[{**r,'mapping_scope':scope} for r in ext]
        annotations,ae=annotate_context(source_path(args.dataset_root,tax,'aliases'),tax,set(context));context_aliases+=ae
        for sid in sorted(selected):
            rs=chosen[chosen.string_id.eq(sid)]
            node_rows.append({'string_id':sid,'network_taxid':tax,'node_role':'WP05_seed' if sid in seeds else 'STRING_context_only',
                'accessions':'|'.join(rs.accession),'protein_name':' | '.join(rs.protein_name) if len(rs) else '',
                'display_alias':annotations[sid][1] if sid in annotations else '',
                'display_name_source':annotations[sid][2] if sid in annotations else '',
                'organism':'Humans / 9606' if tax=='9606' else 'E. coli K12 MG1655 / 511145',
                'mapping_scope':scope if sid in seeds else 'context_from_STRING_links',
                'drugbank_target_verified':False if sid not in seeds else 'role-specific WP05 relation; not necessarily target',
                'sequence_feature_available':bool(len(rs))})
        for graph_type,nset,ed in [('induced_seed',seeds,rows),('expanded_context',selected,ext)]:
            for threshold in THRESHOLDS:
                met,g=network_metrics(nset,ed,threshold);metrics.append({'network_taxid':tax,'graph_type':graph_type,'mapping_scope':scope,**met})
        print(tax,'seed_accessions',len(chosen),'seed_STRING_ids',len(seeds),'induced pairs',len(rows),'context',len(context),flush=True)
    for name,rows in [('ppi_induced_edges.csv',all_edges),('ppi_expanded_edges.csv',expanded),('ppi_nodes.csv',node_rows),
        ('network_metrics.csv',metrics),('score_histogram.csv',score_rows),('context_selection.csv',selection),('context_alias_evidence.csv',context_aliases)]:
        pd.DataFrame(rows).to_csv(QA/name,index=False,encoding='utf-8-sig')
    (QA/'links_manifest.json').write_text(json.dumps(manifests,ensure_ascii=False,indent=2),encoding='utf-8')
    (QA/'network_policy.json').write_text(json.dumps({'thresholds':THRESHOLDS,'neighbors_min_score':NEIGHBOR_MIN_SCORE,
        'neighbors_per_seed':NEIGHBORS_PER_SEED,'context_budget_per_network':CONTEXT_BUDGET,
        'primary_strict_taxon_network':'9606','ecoli_graph_scope':'separate alias-exact exploratory scenario; parent83333 vs substrain511145 not strain-verified',
        'unmatched_and_outside_scope_not_imputed':True,'global_duplicate_count':'not computed; exact pair QC only for retained induced/expanded graphs',
        'score_role':'edge evidence only; score/1000 for descriptive strength; not protein feature'},indent=2),encoding='utf-8')
    print(pd.DataFrame(metrics).to_string(index=False))


if __name__=='__main__':main()
