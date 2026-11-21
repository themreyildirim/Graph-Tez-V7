"""Kayıtlı fit/OOF çıktılarından trainability, kaynak izi ve sonuç örneği; refit yok."""
import json
import numpy as np
import pandas as pd
from wp09_train import ROOT,QA,MODEL,PREP,SEMANTICS,source_labels,restrict_labels,proxy_matrix,write_json,csv,preserve,restore,load_bundle


def main():
    preserve();source=source_labels();parts=pd.read_csv(PREP/'nested_partitions_v1.csv')
    eligible=pd.read_csv(PREP/'prediction_eligibility.csv');usable=set(eligible[eligible.model.eq('B2')&eligible.eligible].drug_id)
    vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
    fittable=json.loads((PREP/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
    stats=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'))
    target_rows=[];provenance=[];boundary=[]
    for context,sub in parts.groupby('context'):
        ids=sorted(set(sub[sub.split.eq('train')].drug_id)&usable);targets=vocab[context]['B2']
        y=proxy_matrix(restrict_labels(source,ids),ids,targets);groups=dict(zip(sub.drug_id,sub.group_id))
        for j,target in enumerate(targets):
            p=int(y[:,j].sum());u=len(ids)-p;pg=len({groups[d] for d,v in zip(ids,y[:,j]) if v})
            fit=target in set(fittable[context]['B2'])
            if fit!=(p>0 and u>0):raise AssertionError('Frozen trainability/source disagreement')
            target_rows.append({'context':context,'class_id':target,'usable_train_drugs':len(ids),'observed_train_positive':p,
                'unknown_train_proxy_NOT_negative':u,'independent_positive_train_groups':pg,'fittable':fit,
                'status':'FITTABLE' if fit else 'NA_single_proxy_train_outcome','semantics':SEMANTICS})
    csv('target_trainability_audit.csv',pd.DataFrame(target_rows))
    for path in sorted(MODEL.glob('*.json')):
        md=json.loads(path.read_text(encoding='utf-8'));context=md['context'];sub=parts[parts.context.eq(context)]
        provenance.append({'job_key':md['job_key'],'context':context,'model':md['model'],
            'classifier_fit_drug_ids':json.dumps(md.get('train_fit_drug_ids',[])),
            'chemistry_scaler_fit_ids':json.dumps(stats[context]['chemistry_fit_drug_ids']),
            'protein_scaler_fit_accessions':json.dumps(stats[context]['protein_fit_accessions']),
            'preprocessing_refit':False,'source':'frozen WP08 transform_fit_sources_and_statistics.json',
            'semantics':SEMANTICS})
        boundary.append({'job_key':md['job_key'],'context':context,'model':md['model'],
            'train_graph_drugs':len(sub[sub.split.eq('train')]),'train_fit_drugs':len(md.get('train_fit_drug_ids',[])),
            'validation_query_drugs':len(sub[sub.split.eq('validation')]),'test_query_drugs':len(sub[sub.split.eq('test')]),
            'train_proteins':len(md.get('protein_ids',[])),'directed_PPI_columns':md.get('effective_directed_PPI_columns'),
            'fitted_PT':len(md.get('fitted_targets',[])),'declared_PT':len(md.get('declared_train_targets',[])),
            'heldout_drug_in_training':False,'side_effect_edges':False})
    csv('feature_fit_provenance.csv',pd.DataFrame(provenance));csv('fold_train_validation_test_scope.csv',pd.DataFrame(boundary))
    null_rows=pd.read_csv(ROOT/'reports/qa/WP09/null_gate_v3/null_preflight_700_three_replicates.csv')
    excluded=[]
    for context,group in null_rows.groupby('context'):
        if group.status.eq('OK_degree_preserving_null').all():continue
        failed=','.join(str(r) for r in group[group.status.ne('OK_degree_preserving_null')].replicate)
        for model in ('G_noPPI','G_realPPI','G_shuffledPPI_R0','G_shuffledPPI_R1','G_shuffledPPI_R2'):
            excluded.append({'context':context,'protocol':group.iloc[0].protocol,'outer_fold':group.iloc[0].outer_fold,
                'inner_fold':group.iloc[0].inner_fold,'model':model,'status':'SKIPPED_SHARED_NULL_FAILURE',
                'failed_null_replicas':failed,'optimizer_steps':0,'prediction_produced':False})
    csv('excluded_inner_jobs.csv',pd.DataFrame(excluded))
    fold=pd.read_csv(QA/'outer_fold_metrics.csv');fit=pd.read_csv(QA/'model_fit_summary.csv')
    outer=fit[fit.inner_fold.eq(0)].copy()
    tail_loss=[]
    for r in outer.itertuples():
        history=pd.read_csv(QA/'history'/(r.job_key+'.csv'))
        tail_loss.append(float(history.iloc[-1].train_BCE_pre_update))
    outer['final_train_BCE_pre_update']=tail_loss
    joined=fold.merge(outer[['protocol','outer_fold','model','best_epoch','optimizer_steps','final_train_BCE_pre_update']],on=['protocol','outer_fold','model'],how='left')
    csv('outer_training_and_evaluation.csv',joined)
    # Example fixed in the run contract before viewing scores: smallest primary paired54 ID.
    keys=pd.read_csv(QA/'comparison_keys.csv');example_id=sorted(keys[keys.protocol.eq('primary')&keys.scope.eq('paired54')].drug_id.unique())[0]
    predictions=pd.read_csv(QA/'oof_predictions.csv');example=predictions[predictions.protocol.eq('primary')&predictions.model.eq('G_realPPI')&predictions.drug_id.eq(example_id)].copy()
    dictionary=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv',usecols=['meddra_cui','term'])
    label_names=dictionary.groupby('meddra_cui').term.agg(lambda x:' / '.join(sorted(set(x)))).to_dict()
    example['PT_name']=example.class_id.map(label_names)
    example=example.sort_values(['score_observed_record_proxy','class_id'],ascending=[False,True]);example['rank']=np.arange(1,len(example)+1)
    csv('example_drug_PT_ranking.csv',example)
    registry=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv');record=registry[registry.drug_id.eq(example_id)].iloc[0]
    chemical=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv');chemical=chemical[chemical.id.eq(example_id)].iloc[0]
    rel=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv');rel=rel[rel.drug_id.eq(example_id)]
    write_json(QA/'example_drug_inputs.json',{'drug_id':example_id,'name':record['name'],'selection':'smallest alphabetically sorted drug_id primary paired54, fixed before results',
        'chemistry_source_values':{c:float(chemical[c]) if pd.notna(chemical[c]) else None for c in ['MW','LogP','HBD','HBA','TPSA']},
        'chemistry_QC_mask':bool(record.chemistry_qc_available),'protein_available':bool(record.protein_modality_available),
        'review_flags':record.review_flags if pd.notna(record.review_flags) else '',
        'protein_role_accessions':{role:sorted(set(rel[rel.role.eq(role)].accession)) for role in ['target','enzyme','transporter','carrier']},
        'actual_model_job':example.iloc[0].model_job_key,'source_provenance':'existing WP04/WP05/WP07 QA; no new feature computation',
        'semantics':SEMANTICS,'score_not_explanation':'ranking illustration, not SHAP/attribution or causal mechanism'})
    print('Trainability/provenance and preselected real query ranking written; no refit')


if __name__=='__main__':main()
