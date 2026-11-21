"""Etiketten bağımsız yapı/gruplama denetimi; gerçek veri bölmesi üretmez."""
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import sys,json,hashlib
import pandas as pd
import networkx as nx

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08'
sys.path.insert(0,str(ROOT/'.deps/rdkit'))
from rdkit import Chem,DataStructs,rdBase
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold


def read(path):return pd.read_csv(ROOT/path,keep_default_na=False)


def write_json(name,obj):
    (QA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def connected_groups(ids,edges,prefix):
    values=list(ids)
    if len(values)!=len(set(values)):raise ValueError('Duplicate canonical ID')
    graph=nx.Graph();graph.add_nodes_from(sorted(values))
    pairs=list(edges)
    if any(a not in graph or b not in graph or a==b for a,b in pairs):raise ValueError('Invalid grouping edge')
    graph.add_edges_from(pairs)
    components=sorted([sorted(c) for c in nx.connected_components(graph)],key=lambda c:c[0])
    return {d:f'{prefix}_{i:03}' for i,c in enumerate(components) for d in c}


def same_nonempty_pairs(frame,column):
    pairs=[]
    for key,group in frame.groupby(column):
        if key: pairs.extend(combinations(sorted(group.drug_id),2))
    return pairs


def greedy_fold_sizes(group_sizes,k):
    """Yalnız büyüklük fizibilitesi; ID/fold ataması veya hedef stratifikasyonu yok."""
    sizes=list(group_sizes)
    if k<2 or k>len(sizes):raise ValueError('Insufficient groups')
    bins=[0]*k
    for size in sorted(sizes,reverse=True):
        index=min(range(k),key=lambda i:(bins[i],i));bins[index]+=int(size)
    return bins


def audit_structures(sources,validation):
    expected=set(sources.id)
    if len(sources)!=len(expected) or set(validation.id)!=expected:raise ValueError('Structure identity mismatch')
    v=validation.set_index('id');generator=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=False)
    rows=[];fps={}
    for row in sources.sort_values('id').itertuples():
        mol=Chem.MolFromSmiles(row.raw_smiles)
        if mol is None:raise ValueError('WP04 parse regression')
        scaffold=MurckoScaffold.MurckoScaffoldSmiles(mol=mol,includeChirality=False)
        rows.append({'drug_id':row.id,'name':row.name,'cid':str(row.cid),
                     'source_inchikey':row.raw_inchikey,'connectivity_block':row.raw_inchikey.split('-')[0],
                     'isomeric_smiles':Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True),
                     'nonisomeric_smiles':Chem.MolToSmiles(mol,canonical=True,isomericSmiles=False),
                     'murcko_scaffold':scaffold,'empty_scaffold':not bool(scaffold),
                     'components':len(Chem.GetMolFrags(mol)), 'WP04_review':not bool(v.loc[row.id,'strict_qc_pass']),
                     'WP04_review_flags':v.loc[row.id,'review_flags']})
        fps[row.id]=generator.GetFingerprint(mol)
    frame=pd.DataFrame(rows);pairs=[]
    for a,b in combinations(sorted(fps),2):
        pairs.append({'drug_id1':a,'drug_id2':b,'morgan2_2048_no_stereo_tanimoto':DataStructs.TanimotoSimilarity(fps[a],fps[b])})
    return frame,pd.DataFrame(pairs)


def main():
    QA.mkdir(parents=True,exist_ok=True)
    previous=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    changed=[p for p,h in previous.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    if changed:raise ValueError(changed)
    sources=read('reports/qa/WP04/structure_sources.csv');v=read('reports/qa/WP04/structure_validation.csv')
    structural,pairs=audit_structures(sources,v);ids=list(structural.drug_id)
    identity=same_nonempty_pairs(structural,'source_inchikey')
    connectivity=same_nonempty_pairs(structural,'connectivity_block')
    nonstereo=same_nonempty_pairs(structural,'nonisomeric_smiles')
    scaffold=same_nonempty_pairs(structural,'murcko_scaffold')
    # İki yapı ölçütü alternatif kontrol; connectivity ana ilacın eşdeğerliği iddiası değildir.
    mandatory=sorted(set(identity+connectivity+nonstereo))
    methods={'primary_drug_only':[], 'connectivity_guard':mandatory,
             'scaffold_guard':sorted(set(mandatory+scaffold))}
    for threshold in (.7,.8,.9):
        close=[(r.drug_id1,r.drug_id2) for r in pairs.itertuples() if r.morgan2_2048_no_stereo_tanimoto>=threshold]
        methods[f'similarity_{threshold:.1f}']=sorted(set(mandatory+close))
    methods['scaffold_or_similarity_0.8']=sorted(set(methods['scaffold_guard']+methods['similarity_0.8']))
    grouping=[];summaries=[];feasibility=[]
    for method,edges in methods.items():
        groups=connected_groups(ids,edges,method)
        grouping.extend({'method':method,'drug_id':drug,'group_id':group,'approved_for_split':False} for drug,group in sorted(groups.items()))
        sizes=pd.Series(groups).value_counts()
        summaries.append({'method':method,'groups':len(sizes),'largest_group':int(sizes.max()),'singleton_groups':int((sizes==1).sum()),
                          'constraint_pairs':len(edges),'cohort':len(ids),'approved_for_split':False})
        for k in (3,5):
            loads=greedy_fold_sizes(sizes,k)
            feasibility.append({'method':method,'hypothetical_k':k,'fold_size_vector_only':json.dumps(loads),
                                'min_fold_size':min(loads),'max_fold_size':max(loads),'largest_group':int(sizes.max()),
                                'note':'Label-free size diagnostic; no drug-fold assignment saved'})
    groups=pd.DataFrame(grouping)
    for name,frame in [('structure_grouping_evidence.csv',structural),('pairwise_structure_similarity.csv',pairs),
                       ('group_candidates.csv',groups),('group_summary.csv',pd.DataFrame(summaries)),('split_size_feasibility.csv',pd.DataFrame(feasibility))]:
        frame.to_csv(QA/name,index=False,encoding='utf-8-sig')
    rel=[]
    for a,b in combinations(ids,2):
        left=structural.set_index('drug_id').loc[a];right=structural.set_index('drug_id').loc[b]
        types=[name for name,col in [('full_inchikey','source_inchikey'),('connectivity','connectivity_block'),('nonstereo','nonisomeric_smiles'),('murcko','murcko_scaffold')]
               if left[col] and left[col]==right[col]]
        if types:rel.append({'drug_id1':a,'name1':left['name'],'drug_id2':b,'name2':right['name'],
                             'matching_representations':'|'.join(types),'review_present':bool(left.WP04_review or right.WP04_review)})
    pd.DataFrame(rel,columns=['drug_id1','name1','drug_id2','name2','matching_representations','review_present']).to_csv(QA/'shared_structure_pairs.csv',index=False,encoding='utf-8-sig')
    salts=read('reports/qa/WP02/salt_parent_links.csv');salts=salts[salts.parent_id.isin(ids)]
    secondary=read('reports/qa/WP02/secondary_ids.csv');secondary=secondary[secondary.parent_id.isin(ids)]
    salts.to_csv(QA/'cohort_salt_parent_evidence.csv',index=False,encoding='utf-8-sig')
    secondary.to_csv(QA/'cohort_secondary_parent_evidence.csv',index=False,encoding='utf-8-sig')
    write_json('structure_audit_summary.json',{'cohort':len(ids),'pairwise_comparisons':len(pairs),'full_identity_pairs':len(identity),
        'connectivity_pairs':len(connectivity),'nonstereo_pairs':len(nonstereo),'same_nonempty_scaffold_pairs':len(scaffold),
        'empty_scaffold_drugs':int(structural.empty_scaffold.sum()),'WP04_review_preserved':int(structural.WP04_review.sum()),
        'salt_links_to_cohort':len(salts),'secondary_links_to_cohort':len(secondary),
        'duplicate_cid_count':int(sources.cid.duplicated().sum()),'rdkit_version':rdBase.rdkitVersion,
        'fingerprint':'Morgan radius=2, 2048 bits, includeChirality=False; full source Mol; grouping QA only',
        'empty_scaffold_policy':'No shared empty-scaffold edge; use identity/connectivity constraints instead',
        'no_parent_standardization':True,'group_methods_are_proposals':True,'actual_split_created':False,
        'prior_files_verified':len(previous)})
    print(json.dumps(json.loads((QA/'structure_audit_summary.json').read_text(encoding='utf-8')),ensure_ascii=True,indent=2))


if __name__=='__main__':main()
