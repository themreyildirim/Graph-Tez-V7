"""WP08 deney öncesi v1: gerçek 5x3 split, train sözlüğü/dönüşüm/graf.

Sınıflandırıcı, negatif örnekleme veya başarım hesabı içermez. Önce kilitli
etiket-kör split üretilir; sonra hedef kapsamı ve train-only dönüşüm hesaplanır.
"""
from pathlib import Path
from collections import defaultdict
import sys,json,hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP08/experimental_preparation'
sys.path.insert(0,str(ROOT/'scripts'))
from wp08_analysis import CHEM,PROTEIN
from wp08_protocol import new_partition_graph

SEED=20261106
ROLES=('target','enzyme','transporter','carrier')
PROTOCOLS={'primary':'connectivity_guard','stress':'scaffold_or_similarity_0.8'}
SPEC={
    'version':'WP08-preparation-v1','status':'FROZEN_FOR_REVIEW_NOT_TRAINING_APPROVED',
    'seed':SEED,'seed_reason':'Project date integer; deterministic convention, no seed search or performance tuning',
    'outer_folds':5,'inner_folds':3,'inner_seed_formula':'seed + 100 * outer_fold',
    'grouping':PROTOCOLS,'allocation':'descending group size; SHA256(seed|group_id) tie order; least-loaded fold, index tie',
    'PT_min_train_drugs':5,'PT_min_train_groups':2,
    'PT_reason':'Prespecified operational support guard; avoids single-group-only targets, not a power/clinical guarantee',
    'support_population':'cohort train vocabulary plus per-model usable-train vocabulary; paired comparison intersection',
    'B1':'5 clean chemistry + chemistry presence mask; absent chemistry -> abstain',
    'B2':'5 chemistry + 4*56 role sequence summaries + 5 input masks; no PPI',
    'missing_blocks':'masked standardized neutral zero only; source missingness retained; not biochemical zero or context feature',
    'all_modalities_absent':'abstain, no prior prediction fallback',
    'protein_universe':'train-linked unique accessions only; separate query features; no test drug in train graph',
    'context':False,'PPI':False,'K12_PPI':False,'ATC':'separate deferred variant; no legacy one-hot',
    'proxy_assumption':'s=observed SIDER record; unknown is not a verified biological negative; approval pending',
    'model_fit_authorized':False,'performance_computation_authorized':False,
}


def read(relative):return pd.read_csv(ROOT/relative,keep_default_na=False)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def write_csv(path,frame):frame.to_csv(path,index=False,encoding='utf-8-sig',lineterminator='\n')


def group_folds(group_map,k,seed):
    buckets=defaultdict(list)
    for drug,group in group_map.items():buckets[group].append(drug)
    if len(buckets)<k:raise ValueError('Insufficient independent groups')
    ordered=sorted(buckets,key=lambda g:(-len(buckets[g]),hashlib.sha256(f'{seed}|{g}'.encode()).hexdigest(),g))
    loads=[0]*k;out={}
    for group in ordered:
        fold=min(range(k),key=lambda i:(loads[i],i));loads[fold]+=len(buckets[group])
        for drug in buckets[group]:out[drug]=fold+1
    return out


def make_partitions(group_candidates):
    assignments=[];partitions=[]
    for protocol,method in PROTOCOLS.items():
        sub=group_candidates[group_candidates.method.eq(method)]
        groups=dict(zip(sub.drug_id,sub.group_id))
        if len(groups)!=62 or len(sub)!=62:raise ValueError('Group cohort mismatch')
        outer=group_folds(groups,5,SEED)
        for drug in sorted(groups):assignments.append({'protocol':protocol,'drug_id':drug,'group_id':groups[drug],'outer_test_fold':outer[drug]})
        for ofold in range(1,6):
            train={d for d in groups if outer[d]!=ofold};test=set(groups)-train
            inner=group_folds({d:groups[d] for d in train},3,SEED+100*ofold)
            for ifold in range(4):
                context=f'{protocol}_o{ofold:02}_'+('final' if ifold==0 else f'i{ifold:02}')
                for drug in sorted(groups):
                    split='test' if drug in test else 'validation' if ifold and inner[drug]==ifold else 'train'
                    partitions.append({'context':context,'protocol':protocol,'outer_fold':ofold,'inner_fold':ifold,
                                       'drug_id':drug,'group_id':groups[drug],'split':split})
    return pd.DataFrame(assignments),pd.DataFrame(partitions)


def freeze_partitions():
    """Bu adım hedef dosyalarını açmaz. Değişen config/hash v1'i ezemez."""
    group_path=ROOT/'reports/qa/WP08/group_candidates.csv'
    lock={'specification':SPEC,'group_source_sha256':sha(group_path)}
    canonical=json.dumps(lock,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    lock['specification_sha256']=hashlib.sha256(canonical).hexdigest()
    lock_path=QA/'split_lock_v1.json'
    if lock_path.exists() and json.loads(lock_path.read_text(encoding='utf-8'))!=lock:
        raise RuntimeError('Frozen v1 differs: do not overwrite; a justified new version is required')
    outer,parts=make_partitions(read('reports/qa/WP08/group_candidates.csv'))
    for name,frame in [('outer_membership_v1.csv',outer),('nested_partitions_v1.csv',parts)]:
        path=QA/name;payload=frame.to_csv(index=False,lineterminator='\n').encode('utf-8-sig')
        if path.exists() and path.read_bytes()!=payload:raise RuntimeError('Frozen membership differs')
        if not path.exists():path.write_bytes(payload)
    if not lock_path.exists():write_json(lock_path,lock)
    manifests={n:sha(QA/n) for n in ['split_lock_v1.json','outer_membership_v1.csv','nested_partitions_v1.csv']}
    path=QA/'frozen_split_manifest.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=manifests:raise RuntimeError('Split manifest conflict')
    if not path.exists():write_json(path,manifests)
    return outer,parts


def support_counts(labels,train_ids,groups):
    frame=labels[labels.drug_id.isin(set(train_ids))][['drug_id','class_id']].copy()
    if frame.duplicated(['drug_id','class_id']).any():raise ValueError('Duplicate training positive')
    frame['group_id']=frame.drug_id.map(groups)
    if frame.group_id.isna().any():raise ValueError('Missing training group')
    return frame.groupby('class_id').agg(drugs=('drug_id','nunique'),groups=('group_id','nunique'))


def candidate_vocabulary(labels,train_ids,groups,min_drugs=5,min_groups=2):
    counts=support_counts(labels,train_ids,groups)
    return sorted(counts[(counts.drugs>=min_drugs)&(counts.groups>=min_groups)].index)


def availability(masks):
    m=masks.set_index('drug_id')
    result=[]
    for drug,row in m.iterrows():
        for model in ('B1','B2'):
            eligible=bool(row.chemistry_qc_available if model=='B1' else row.chemistry_qc_available or row.protein_modality_available)
            reason='' if eligible else 'abstain_no_QC_approved_chemistry' if model=='B1' else 'abstain_no_personalized_input'
            result.append({'drug_id':drug,'name':row['name'],'model':model,'eligible':eligible,'abstention_reason':reason,
                           'chemistry_available':bool(row.chemistry_qc_available),'protein_available':bool(row.protein_modality_available),
                           'molecule_review':bool(row.molecule_review),'review_flags':row.review_flags,'cohort_retained':True})
    return pd.DataFrame(result)


def fit_statistics(chemistry,protein_features,typed,train_ids,chem_available):
    train=set(train_ids)
    chem_ids=sorted(train&set(chem_available))
    protein_ids=sorted(set(typed[typed.drug_id.isin(train)].accession))
    if not chem_ids or not protein_ids:raise ValueError('No train source for standardization')
    x=chemistry.loc[chem_ids,CHEM];p=protein_features.loc[protein_ids,PROTEIN]
    if x.isna().any().any() or p.isna().any().any():raise ValueError('Input feature missingness inconsistent with mask')
    def stats(frame):
        scale=frame.std(ddof=0);constant=list(scale[scale.eq(0)].index)
        return {'mean':frame.mean().to_dict(),'scale':scale.replace(0,1).to_dict(),'constant_fields':constant,'ddof':0}
    return {'chemistry_fit_drug_ids':chem_ids,'protein_fit_accessions':protein_ids,
            'chemistry':stats(x),'protein':stats(p),'transform_only_heldout':True}


def feature_schema():
    return {'B1':['chem__'+x for x in CHEM]+['mask__chemistry'],
            'B2':['chem__'+x for x in CHEM]+[role+'__'+x for role in ROLES for x in PROTEIN]+
                 ['mask__chemistry']+['mask__'+role for role in ROLES]}


def transformed_features(ids,chemistry,pf,typed,masks,statistics):
    """Dönüşüm sadece train istatistiklerini kullanır; absent blok maskelenir."""
    ids=list(ids);m=masks.set_index('drug_id');out=np.zeros((len(ids),229+5),dtype=np.float64)
    cm=pd.Series(statistics['chemistry']['mean']);cs=pd.Series(statistics['chemistry']['scale'])
    pm=pd.Series(statistics['protein']['mean']);ps=pd.Series(statistics['protein']['scale'])
    for i,drug in enumerate(ids):
        if bool(m.loc[drug,'chemistry_qc_available']):
            out[i,:5]=((chemistry.loc[drug,CHEM]-cm)/cs).to_numpy();out[i,229]=1
        for j,role in enumerate(ROLES):
            acc=sorted(set(typed[typed.drug_id.eq(drug)&typed.role.eq(role)].accession))
            if acc:
                values=(pf.loc[acc,PROTEIN]-pm)/ps
                out[i,5+j*56:5+(j+1)*56]=values.mean().to_numpy();out[i,230+j]=1
    if not np.isfinite(out).all():raise ValueError('Nonfinite prepared feature')
    return {'B1':np.column_stack((out[:,:5],out[:,229])),'B2':out}


def build_target_plan(labels,parts,coverage):
    eligible={model:set(coverage[coverage.model.eq(model)&coverage.eligible].drug_id) for model in ('B1','B2')}
    records=[];vocabs={};counts=[]
    for context,sub in parts.groupby('context',sort=True):
        train=set(sub[sub.split.eq('train')].drug_id);groups=dict(zip(sub.drug_id,sub.group_id))
        views={'cohort':train,'B1':train&eligible['B1'],'B2':train&eligible['B2']}
        supports={scope:support_counts(labels,ids,groups) for scope,ids in views.items()}
        selected={scope:candidate_vocabulary(labels,ids,groups) for scope,ids in views.items()}
        selected['paired']=sorted(set(selected['B1'])&set(selected['B2']))
        vocabs[context]=selected
        for scope,frame in supports.items():
            for cls,row in frame.iterrows():records.append({'context':context,'scope':scope,'class_id':cls,
                'train_positive_drugs':int(row.drugs),'train_positive_groups':int(row.groups),
                'selected_5_drugs_2_groups':cls in selected[scope]})
        for scope,classes in selected.items():counts.append({'context':context,'scope':scope,'PT_classes':len(classes),
            'protocol':sub.iloc[0].protocol,'outer_fold':int(sub.iloc[0].outer_fold),'inner_fold':int(sub.iloc[0].inner_fold)})
    return pd.DataFrame(records),vocabs,pd.DataFrame(counts)


def main():
    QA.mkdir(parents=True,exist_ok=True)
    prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    if any(sha(ROOT/p)!=h for p,h in prior.items()):raise RuntimeError('Prior output changed')
    outer,parts=freeze_partitions() # etiketten ÖNCE değiştirilemez v1 kilidi
    paths=['reports/qa/WP08/group_candidates.csv','reports/qa/WP07/drug_modality_QA.csv',
           'reports/qa/WP04/chemical_features_clean.csv','reports/qa/WP05/protein_features.csv',
           'reports/qa/WP05/protein_registry.csv','reports/qa/WP05/drug_protein_edges.csv',
           'reports/qa/WP03/drug_pt_positives.csv','reports/qa/WP03/historical_category_projection_audit.csv']
    write_json(QA/'input_manifest.json',{p:sha(ROOT/p) for p in paths})
    masks=read(paths[1]);ids=sorted(masks.drug_id)
    chemistry=pd.read_csv(ROOT/paths[2]).set_index('id');pf=pd.read_csv(ROOT/paths[3]).set_index('accession')
    registry=read(paths[4]);typed=read(paths[5])
    if list(chemistry.columns)!=CHEM or list(pf.columns)!=PROTEIN:raise ValueError('Frozen feature order mismatch')
    coverage=availability(masks);write_csv(QA/'prediction_eligibility.csv',coverage)
    chem_available=set(coverage[coverage.model.eq('B1')&coverage.eligible].drug_id)
    pt=read(paths[6]);pt=pt[pt.conservative & pt.id.isin(ids)][['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'class_id'})
    support,vocabs,counts=build_target_plan(pt,parts,coverage)
    write_csv(QA/'train_PT_support.csv',support);write_json(QA/'train_vocabularies.json',vocabs);write_csv(QA/'vocabulary_counts.csv',counts)
    historical=read(paths[7]);historical=historical[historical.conservative & historical.id.isin(ids)][['id','category']].drop_duplicates().rename(columns={'id':'drug_id','category':'class_id'})
    secondary_classes=sorted(historical.class_id.unique())
    write_json(QA/'historical30_reference.json',{'classes':secondary_classes,'semantic_status':'historical comparison; clinical warnings preserved','no_new_merge_or_selection':True})
    fit_plans={};graphs={};graph_counts=[];context_counts=[];evaluation=[];candidate_pairs=[]
    schema=feature_schema();write_json(QA/'feature_schema_v1.json',{'version':'WP08-input-prep-v1','features':schema,'roles':ROLES,
         'source_ids_in_X':False,'target_features_in_X':False,'PPI':False,'context':False,
         'missing_value_interpretation':'masked standardized neutral block, not observed biochemical zero',
         'model_training_approved':False})
    features_dir=QA/'features';features_dir.mkdir(exist_ok=True)
    for context,sub in parts.groupby('context',sort=True):
        train=set(sub[sub.split.eq('train')].drug_id);held=set(ids)-train
        stats=fit_statistics(chemistry,pf,typed,train,chem_available);fit_plans[context]=stats
        arrays=transformed_features(ids,chemistry,pf,typed,masks,stats)
        np.savez_compressed(features_dir/(context+'.npz'),drug_ids=np.array(ids),**arrays)
        graph=new_partition_graph(ids,typed,registry,train,held,'train_linked_only')
        graph.purpose='WP08_prepared_train_only_no_model_fit';graphs[context]=graph
        for edge_type in graph.edge_types:graph_counts.append({'context':context,'relation':edge_type[1],
            'source_type':edge_type[0],'target_type':edge_type[2],'edge_count':graph[edge_type].num_edges})
        context_counts.append({'context':context,'protocol':sub.iloc[0].protocol,'outer_fold':int(sub.iloc[0].outer_fold),
            'inner_fold':int(sub.iloc[0].inner_fold),'train_drugs':len(train),'validation_drugs':int(sub.split.eq('validation').sum()),
            'test_drugs':int(sub.split.eq('test').sum()),'train_graph_drugs':graph['drug'].num_nodes,
            'train_graph_proteins':graph['protein'].num_nodes,'train_graph_edges':sum(graph[t].num_edges for t in graph.edge_types),
            'chemistry_fit_drugs':len(stats['chemistry_fit_drug_ids']),'protein_fit_accessions':len(stats['protein_fit_accessions'])})
        # Değerlendirme olanaklılığı yalnız kayıt kapsamı, skor/başarım yok.
        for model in ('B1','B2'):
            eligible=set(coverage[coverage.model.eq(model)&coverage.eligible].drug_id)
            classes=set(vocabs[context][model])
            for split in ('train','validation','test'):
                split_ids=set(sub[sub.split.eq(split)].drug_id);usable=split_ids&eligible
                obs=pt[pt.drug_id.isin(usable)&pt.class_id.isin(classes)]
                support_by_class=obs.groupby('class_id').drug_id.nunique().reindex(sorted(classes),fill_value=0)
                evaluation.append({'context':context,'model':model,'split':split,'cohort_drugs':len(split_ids),'eligible_drugs':len(usable),
                    'abstained_drugs':len(split_ids-usable),'train_selected_PT_classes':len(classes),'observed_positive_pairs':len(obs),
                    'unobserved_pairs_NOT_verified_negatives':len(usable)*len(classes)-len(obs),
                    'classes_no_observed_positive':int(support_by_class.eq(0).sum()),
                    'classes_all_observed_positive':int(support_by_class.eq(len(usable)).sum()) if usable else 0,
                    'proxy_AUROC_evaluable_classes':int((support_by_class.gt(0)&support_by_class.lt(len(usable))).sum()),
                    'metric_values_computed':False,'meaning':'observed-record support only; unknown not verified negative'})
    sys.path.insert(0,str(ROOT/'.deps/pyg'));import torch
    torch.save(graphs,QA/'train_only_graphs_v1.pt')
    write_json(QA/'transform_fit_sources_and_statistics.json',fit_plans)
    write_csv(QA/'context_summary.csv',pd.DataFrame(context_counts));write_csv(QA/'graph_edge_counts.csv',pd.DataFrame(graph_counts))
    write_csv(QA/'metric_evaluability_NO_scores.csv',pd.DataFrame(evaluation))
    write_json(QA/'preparation_summary.json',{'cohort':len(ids),'protocols':PROTOCOLS,'outer_folds':5,'inner_folds':3,
       'fit_contexts':len(graphs),'graph_objects_new':len(graphs),'feature_dimensions':{m:len(c) for m,c in schema.items()},
       'B1_eligible':int(coverage[coverage.model.eq('B1')].eligible.sum()),'B2_eligible':int(coverage[coverage.model.eq('B2')].eligible.sum()),
       'Methenamine':'abstain for B1 and B2; retained in inventory','complete_case_only_sensitivity':53,
       'seed':SEED,'min_positive_train_drugs':5,'min_positive_train_groups':2,'training_run':False,
       'negative_sampling':False,'performance_values_computed':False,'WP08_closed':False,'WP09_started':False,
       'prior_files_preserved':len(prior),'model_fit_approval_pending':True})
    print('Prepared',len(graphs),'train-only contexts. No classifier or performance computation.')


if __name__=='__main__':main()
