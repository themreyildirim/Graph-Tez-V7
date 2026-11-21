"""Keşifsel B0_frequency_reference_v1: yalnız train observed-record sıklığı.

Kimya/dizi/PPI/ATC değerleri okunmaz. Eligibility yalnız eşleştirilmiş train
popülasyonu kimliklerini tanımlar. B1/B2 kodu çalıştırılmaz veya fit edilmez.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'reports/qa/WP08/experimental_preparation';BASE=ROOT/'reports/qa/WP08/baseline_v1'
QA=ROOT/'reports/qa/WP08/B0_frequency_reference_v1'
SEMANTICS='Exploratory train-frequency observed-record ranking reference; unknown is NOT verified negative; not personalized or clinical risk'
POLICY={
    'version':'B0_frequency_reference_v1','exploratory_after_B1_B2_results':True,
    'accepted_original_primary_paired_AP':{'B1':0.6556,'B2':0.6262},
    'score_formula':'count(unique train drugs with observed PT record) / number of defined train drugs',
    'smoothing':None,'score_transform':'identity','hyperparameter_search':False,
    'train_populations':{'B0_all_train':'all train IDs, including drugs without biological inputs',
        'B0_like_B1':'train IDs intersect frozen B1 input eligibility',
        'B0_like_B2':'train IDs intersect frozen B2 input eligibility'},
    'intrinsic_eligibility':'all 62 inventory IDs; only a population reference, not personalized prediction',
    'Methenamine':'B0 population reference allowed; B1/B2 abstention remains unchanged; excluded from matched comparisons',
    'targets':'frozen cohort train PT dictionary; matched evaluations use EXACT existing B1/B2 scored target keys',
    'no_new_target_selection':True,'no_clinical_negative_claim':True,
    'scope':['own_B1','own_B2','paired54','complete_case53','B0_all62_reference_ONLY'],
    'main_comparisons':['B1 minus B0_like_B1','B2 minus B0_like_B2 on paired54'],
    'sensitivity':'B1/B2 minus B0_all_train; complete-case53 same fitted models, no retraining',
    'bootstrap_reps':1000,'bootstrap_min_valid':800,'seed':20261106,
    'bootstrap_seed':'20261106+9000+protocol_index (same frozen baseline draws)',
    'bootstrap_unit':'locked structural group; paired identical draws',
    'CI_scope':'conditional on fixed OOF models and frequency estimates; no full retraining bootstrap',
    'PPI_ATC_chemistry_sequence_values_read':False,'B1_B2_refit_or_retuning':False,
    'WP08_closed':False,'WP09_started':False,'semantics':SEMANTICS,
}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,obj):
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(tuple,list)):return [clean(v) for v in x]
        if isinstance(x,np.generic):return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x):return None
        return x
    path.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def write_csv(path,frame):frame.to_csv(path,index=False,encoding='utf-8-sig',lineterminator='\n')


def check_preservation():
    previous=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    bad=[p for p,h in previous.items() if sha(ROOT/p)!=h]
    if bad:raise RuntimeError(f'Existing output changed: {bad}')
    return len(previous)


def freeze_policy():
    """B0 sonucu hesaplanmadan yazılır; B1/B2 sonuçlarının görülmüş olduğu gizlenmez."""
    path=QA/'policy_before_B0_results.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=POLICY:
        raise RuntimeError('Do not alter B0 v1 after results; justified new version required')
    if not path.exists():write_json(path,POLICY)
    return sha(path)


def frequency_estimate(observed,train_ids,targets):
    """Girdi şeması sadece drug_id, pt_cui. Heldout satırlar önce filtrelenir."""
    if set(observed.columns)!={'drug_id','pt_cui'}:raise ValueError('B0 accepts only record identity columns')
    ids=list(train_ids);classes=list(targets)
    if not ids or len(ids)!=len(set(ids)) or len(classes)!=len(set(classes)):raise ValueError('Invalid train/target IDs')
    local=observed[observed.drug_id.isin(set(ids))]
    if local.duplicated(['drug_id','pt_cui']).any():raise ValueError('Duplicate train record')
    counts=local.groupby('pt_cui').drug_id.nunique().reindex(classes,fill_value=0)
    return pd.DataFrame({'pt_cui':classes,'observed_train_drugs':counts.to_numpy(dtype=int),
                         'train_drugs':len(ids),'frequency_score':counts.to_numpy(dtype=float)/len(ids)})


def main():
    QA.mkdir(parents=True,exist_ok=True);previous=check_preservation();policy_sha=freeze_policy()
    if (QA/'frequency_complete.json').exists():raise RuntimeError('B0 v1 already estimated; no result-driven re-estimation')
    source_paths=[PREP/'nested_partitions_v1.csv',PREP/'outer_membership_v1.csv',PREP/'prediction_eligibility.csv',
        PREP/'train_vocabularies.json',PREP/'frozen_split_manifest.json',PREP/'complete_case_53_inventory_ONLY.csv',
        ROOT/'reports/qa/WP03/drug_pt_positives.csv',BASE/'oof_predictions.csv',BASE/'selected_C.csv']
    write_json(QA/'input_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in source_paths})
    parts=pd.read_csv(PREP/'nested_partitions_v1.csv')
    # Salt ID/eligibility; numeric chemistry/protein/ATC fields never opened.
    eligibility=pd.read_csv(PREP/'prediction_eligibility.csv',usecols=['drug_id','model','eligible'])
    vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
    source=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['id','meddra_cui','conservative'])
    observed=source[source.conservative][['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'pt_cui'})
    eligible={model:set(eligibility[eligibility.model.eq(model)&eligibility.eligible].drug_id) for model in ('B1','B2')}
    population_rows=[];rows=[];query=[];status=[]
    for context,sub in parts.groupby('context',sort=True):
        train=set(sub[sub.split.eq('train')].drug_id)
        populations={'B0_all_train':train,'B0_like_B1':train&eligible['B1'],'B0_like_B2':train&eligible['B2']}
        for reference,population in populations.items():
            ids=sorted(population);targets=vocab[context]['cohort'];scores=frequency_estimate(observed,ids,targets)
            population_rows.extend({'context':context,'reference':reference,'train_drug_id':d,'semantics':SEMANTICS} for d in ids)
            meta={'context':context,'protocol':sub.iloc[0].protocol,'outer_fold':int(sub.iloc[0].outer_fold),
                  'inner_fold':int(sub.iloc[0].inner_fold),'reference':reference,'semantics':SEMANTICS}
            rows.extend({**meta,**r._asdict()} for r in scores.itertuples(index=False))
            if int(sub.iloc[0].inner_fold)==0:
                for drug in sorted(sub[sub.split.eq('test')].drug_id):
                    query.extend({**meta,'drug_id':drug,**r._asdict()} for r in scores.itertuples(index=False))
                    status.append({**meta,'drug_id':drug,'status':'POPULATION_FREQUENCY_REFERENCE_NOT_PERSONALIZED',
                        'biological_input_required':False,'inventory_retained':True})
    write_csv(QA/'train_frequency_estimates.csv',pd.DataFrame(rows));write_csv(QA/'train_population_ids.csv',pd.DataFrame(population_rows))
    write_csv(QA/'B0_outer_query_scores.csv',pd.DataFrame(query));write_csv(QA/'B0_status_all62.csv',pd.DataFrame(status))
    write_json(QA/'frequency_complete.json',{'version':POLICY['version'],'policy_sha256':policy_sha,'prior_files_verified':previous,
        'contexts':parts.context.nunique(),'population_estimates':parts.context.nunique()*3,
        'formula':'observed unique train count / train N; no smoothing/transform/tuning',
        'no_B1_B2_refit':True,'semantics':SEMANTICS})
    check_preservation();print('B0 train frequencies completed for 40 contexts / 120 populations. Existing outputs unchanged.')


if __name__=='__main__':main()
