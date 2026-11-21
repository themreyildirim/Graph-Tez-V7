"""WP09 design-v1: frozen split + train-only biyolojik girdiler; hedef/öğrenme yok."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'reports/qa/WP09/design_v1'
PREP=ROOT/'reports/qa/WP08/experimental_preparation'
ROLES=('target','enzyme','transporter','carrier')
CHEM=('MW','LogP','HBD','HBA','TPSA')
THRESHOLDS=(400,700,900)


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def json_write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def csv_write(path,frame):
    frame.to_csv(path,index=False,encoding='utf-8-sig',lineterminator='\n')


def snapshot():
    QA.mkdir(parents=True,exist_ok=True)
    target=QA/'prior_outputs_sha256.json'
    if target.exists():raise RuntimeError('WP09 design-v1 snapshot already frozen')
    previous={}
    for directory in ('docs','reports','notebooks','scripts','tests','configs','models'):
        for path in sorted((ROOT/directory).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:continue
            relative=path.relative_to(ROOT).as_posix()
            if '/WP09/' in relative or path.name.lower().startswith(('wp09','test_wp09')):continue
            previous[relative]=sha(path)
    json_write(target,previous)
    print(f'WP09 preservation snapshot: {len(previous)} prior files')


def preserve():
    previous=json.loads((QA/'prior_outputs_sha256.json').read_text(encoding='utf-8'))
    extra=QA/'prior_WP09_draft_inputs_sha256.json'
    if extra.exists():previous.update(json.loads(extra.read_text(encoding='utf-8')))
    bad=[p for p,h in previous.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if bad:raise AssertionError(f'Previous output changed: {bad}')
    return len(previous)


def load_sources():
    paths={
        'partitions':PREP/'nested_partitions_v1.csv','eligibility':PREP/'prediction_eligibility.csv',
        'stats':PREP/'transform_fit_sources_and_statistics.json','schema':PREP/'feature_schema_v1.json',
        'masks':ROOT/'reports/qa/WP07/drug_modality_QA.csv',
        'chem':ROOT/'reports/qa/WP04/chemical_features_clean.csv',
        'protein':ROOT/'reports/qa/WP05/protein_features.csv',
        'relations':ROOT/'reports/qa/WP05/drug_protein_edges.csv',
        'mapping':ROOT/'reports/qa/WP06/protein_string_mapping.csv',
        'ppi':ROOT/'reports/qa/WP06/strict_taxon_induced_edges.csv'}
    schema=json.loads(paths['schema'].read_text(encoding='utf-8'))
    protein_columns=[x.removeprefix('target__') for x in schema['features']['B2'] if x.startswith('target__')]
    if len(protein_columns)!=56 or len(set(protein_columns))!=56:raise ValueError('Frozen 56-feature schema required')
    data={name:pd.read_csv(path) for name,path in paths.items() if path.suffix=='.csv'}
    data['stats']=json.loads(paths['stats'].read_text(encoding='utf-8'))
    data['protein_columns']=protein_columns
    data['paths']=paths
    if list(data['protein'].columns)!=['accession']+protein_columns:raise ValueError('Protein feature allowlist mismatch')
    if not np.isfinite(data['protein'][protein_columns].to_numpy()).all():raise ValueError('Unvalidated protein features')
    if data['relations'].duplicated(['drug_id','accession','role']).any():raise ValueError('Duplicate typed relation')
    if not set(data['relations'].role)<=set(ROLES):raise ValueError('Unknown relation or reverse/target edge')
    if not data['relations'].sequence_available.all():raise ValueError('Sequence-less relation cannot enter protein encoder')
    if set(data['relations'].accession)-set(data['protein'].accession):raise ValueError('Feature-less/context accession')
    if not data['ppi'].network_taxid.eq(9606).all() or not data['ppi'].mapping_scope.eq('exact_taxon').all():
        raise ValueError('Human strict-taxID PPI only')
    strict=data['mapping'][data['mapping'].strict_taxon_match & data['mapping'].network_taxid.eq(9606)]
    if len(strict)!=63 or strict.string_id.duplicated().any():raise ValueError('63 unambiguous human mappings required')
    data['strict']=strict
    return data


def edge_array(pairs):
    return np.asarray(list(pairs),dtype=np.int64).reshape(-1,2).T.copy()


def ppi_pairs(data,accessions,threshold):
    if threshold not in THRESHOLDS:raise ValueError('Explicit reviewed threshold required')
    if not data['ppi'].network_taxid.eq(9606).all() or not data['ppi'].mapping_scope.eq('exact_taxon').all():
        raise ValueError('Conditional/nonhuman PPI prohibited')
    strict=data['strict'];sid=dict(zip(strict.string_id,strict.accession));indices={a:i for i,a in enumerate(accessions)}
    pairs=set()
    for row in data['ppi'].itertuples():
        if row.score_conflict or row.combined_score<threshold:continue
        if row.protein1 not in sid or row.protein2 not in sid:raise ValueError('Undeclared human STRING node')
        a,b=sid[row.protein1],sid[row.protein2]
        if a in indices and b in indices:
            i,j=sorted((indices[a],indices[b]))
            if i==j:raise ValueError('PPI self-loop')
            if (i,j) in pairs:raise ValueError('Duplicate PPI pair')
            pairs.add((i,j))
    return sorted(pairs)


def standardize_proteins(data,accessions,stats):
    cols=data['protein_columns'];frame=data['protein'].set_index('accession')
    x=frame.loc[list(accessions),cols]
    result=((x-pd.Series(stats['protein']['mean']))/pd.Series(stats['protein']['scale'])).loc[:,cols].to_numpy(dtype=np.float64)
    if not np.isfinite(result).all():raise ValueError('Protein transform invalid')
    return result


def drug_arrays(data,ids,pool,stats):
    masks=data['masks'].set_index('drug_id');chem=data['chem'].set_index('id')
    relation=data['relations'];positions={a:i for i,a in enumerate(pool)}
    x=np.zeros((len(ids),5),dtype=np.float64);present=np.zeros((len(ids),5),dtype=bool)
    role_edges={role:[] for role in ROLES}
    for i,drug in enumerate(ids):
        if bool(masks.loc[drug,'chemistry_qc_available']):
            x[i]=((chem.loc[drug,list(CHEM)]-pd.Series(stats['chemistry']['mean']))/pd.Series(stats['chemistry']['scale'])).loc[list(CHEM)]
            present[i,0]=True
        for j,role in enumerate(ROLES):
            acc=sorted(set(relation[relation.drug_id.eq(drug)&relation.role.eq(role)].accession))
            if set(acc)-set(pool):raise ValueError('Unknown role protein index')
            role_edges[role].extend((i,positions[a]) for a in acc);present[i,j+1]=bool(acc)
    return {'drug_ids':np.asarray(ids,dtype=str),'chemistry':x,'masks':present,'eligible':present.any(axis=1),
        **{'role_'+role:edge_array(pairs) for role,pairs in role_edges.items()}}


def build_context(data,context,include_query=True):
    sub=data['partitions'][data['partitions'].context.eq(context)]
    if len(sub)!=62 or sub.drug_id.duplicated().any():raise ValueError('Frozen 62-drug partition required')
    train=sorted(sub[sub.split.eq('train')].drug_id)
    heldout=sorted(sub[sub.split.ne('train')].drug_id)
    stats=data['stats'][context]
    accessions=sorted(set(data['relations'][data['relations'].drug_id.isin(train)].accession))
    if accessions!=stats['protein_fit_accessions']:raise ValueError('Train-only protein fit sources changed')
    if set(stats['chemistry_fit_drug_ids'])-set(train):raise ValueError('Heldout scaler fit source')
    graph={'protein_ids':np.asarray(accessions,dtype=str),'protein_x':standardize_proteins(data,accessions,stats),
           **drug_arrays(data,train,accessions,stats)}
    for threshold in THRESHOLDS:
        pairs=ppi_pairs(data,accessions,threshold)
        graph[f'ppi_pairs_{threshold}']=edge_array(pairs)
    eligible=data['eligibility'][data['eligibility'].model.eq('B2')].set_index('drug_id').eligible
    if not np.array_equal(graph['eligible'],eligible.loc[list(graph['drug_ids'])].to_numpy()):raise ValueError('Frozen train B2 eligibility differs')
    if not include_query:return graph,None
    query_accessions=sorted(set(data['relations'][data['relations'].drug_id.isin(heldout)].accession)-set(accessions))
    query={'unseen_protein_ids':np.asarray(query_accessions,dtype=str),
        'unseen_protein_x':standardize_proteins(data,query_accessions,stats),
        'split':np.asarray([sub.set_index('drug_id').loc[d,'split'] for d in heldout],dtype=str),
        **drug_arrays(data,heldout,accessions+query_accessions,stats)}
    if not np.array_equal(query['eligible'],eligible.loc[list(query['drug_ids'])].to_numpy()):raise ValueError('Frozen query B2 eligibility differs')
    return graph,query


def validate_bundle(graph,query=None):
    expected={'protein_ids','protein_x','drug_ids','chemistry','masks','eligible'}
    expected|={'role_'+r for r in ROLES}|{f'ppi_pairs_{t}' for t in THRESHOLDS}
    if set(graph)!=expected:raise ValueError('Unexpected graph field/label/edge')
    n=len(graph['protein_ids']);d=len(graph['drug_ids'])
    if len(set(graph['protein_ids']))!=n or len(set(graph['drug_ids']))!=d:raise ValueError('Duplicate node ID')
    if graph['protein_x'].shape!=(n,56) or not np.isfinite(graph['protein_x']).all():raise ValueError('56 valid protein fields required')
    if graph['chemistry'].shape!=(d,5) or graph['masks'].shape!=(d,5) or graph['masks'].dtype!=bool:raise ValueError('Drug input schema')
    for threshold in THRESHOLDS:
        pairs=graph[f'ppi_pairs_{threshold}']
        if pairs.ndim!=2 or pairs.shape[0]!=2 or not np.issubdtype(pairs.dtype,np.integer):raise ValueError('PPI schema')
        if pairs.size and (pairs.min()<0 or pairs.max()>=n or not (pairs[0]<pairs[1]).all()):raise ValueError('Invalid PPI endpoint')
        if len(set(map(tuple,pairs.T)))!=pairs.shape[1]:raise ValueError('Duplicate PPI pair')
    if query is not None:
        qexpected={'unseen_protein_ids','unseen_protein_x','split','drug_ids','chemistry','masks','eligible'}|{'role_'+r for r in ROLES}
        if set(query)!=qexpected:raise ValueError('Unexpected query input/label')
        if set(query['drug_ids'])&set(graph['drug_ids']):raise ValueError('Query drug in training graph')
        if set(query['unseen_protein_ids'])&set(graph['protein_ids']):raise ValueError('Seen protein duplicated as unseen')
        if query['unseen_protein_x'].shape!=(len(query['unseen_protein_ids']),56):raise ValueError('Query protein schema')
    for block,pool_size in [(graph,n)]+([] if query is None else [(query,n+len(query['unseen_protein_ids']))]):
        d=len(block['drug_ids'])
        if not np.array_equal(block['eligible'],block['masks'].any(axis=1)):raise ValueError('Eligibility inconsistent')
        if not np.isfinite(block['chemistry']).all() or (block['chemistry'][~block['masks'][:,0]]!=0).any():raise ValueError('Masked chemistry schema')
        for j,role in enumerate(ROLES):
            edges=block['role_'+role]
            if edges.ndim!=2 or edges.shape[0]!=2 or not np.issubdtype(edges.dtype,np.integer):raise ValueError('Role edge schema')
            if edges.size and (edges.min()<0 or edges[0].max()>=d or edges[1].max()>=pool_size):raise ValueError('Role endpoint range')
            if len(set(map(tuple,edges.T)))!=edges.shape[1]:raise ValueError('Duplicate typed relation')
            present=np.bincount(edges[0],minlength=d)>0
            if not np.array_equal(present,block['masks'][:,j+1]):raise ValueError('Role mask contradiction')
    return True


def main():
    count=preserve();data=load_sources()
    if (QA/'preparation_complete.json').exists():raise RuntimeError('Do not overwrite WP09 design-v1 prepared data')
    json_write(QA/'input_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in data['paths'].values()})
    folder=QA/'folds';folder.mkdir(exist_ok=True)
    contexts=[]
    for context in sorted(data['partitions'].context.unique()):
        graph,query=build_context(data,context)
        validate_bundle(graph,query)
        np.savez_compressed(folder/(context+'_train.npz'),**graph)
        np.savez_compressed(folder/(context+'_query.npz'),**query)
        contexts.append({'context':context,'train_drugs':len(graph['drug_ids']),'train_proteins':len(graph['protein_ids']),
            'query_drugs':len(query['drug_ids']),'query_unseen_sequence_proteins':len(query['unseen_protein_ids']),
            'training_authorized':False,'targets_in_graph':False})
    csv_write(QA/'context_inventory.csv',pd.DataFrame(contexts))
    json_write(QA/'prepared_artifact_manifest.json',{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(folder.glob('*.npz'))})
    json_write(QA/'preparation_complete.json',{'version':'WP09-design-v1','prior_files_verified':count,
        'contexts':40,'NPZ_files':80,'thresholds':list(THRESHOLDS),'selected_threshold':None,
        'no_labels_or_PT_nodes':True,'new_scaler_fit':False,'WP07_or_WP08_pt_loaded':False,
        'training_authorized':False,'query_policy':'unseen accession self-only; no query-to-training messages'})
    preserve();print('40 new train-only source-table bundles + separate queries prepared; no training or labels')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['snapshot','prepare','preserve'])
    action=parser.parse_args().action
    if action=='snapshot':snapshot()
    elif action=='prepare':main()
    else:print(preserve())
