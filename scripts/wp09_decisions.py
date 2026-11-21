"""Etiket bağımsız topoloji/null bulguları: sürümlü öneri, eğitim onayı değildir."""
import json
import copy
import numpy as np
import pandas as pd
from wp09_data import ROOT,QA,csv_write,json_write,sha,preserve


def main():
    preserve()
    quality=pd.read_csv(QA/'shuffle_quality.csv');rows=[]
    for row in quality.itertuples():
        with np.load(QA/'folds'/(row.context+'_train.npz'),allow_pickle=False) as graph:
            edges=graph[f'ppi_pairs_{row.threshold}'];n=len(graph['protein_ids'])
        degrees=np.bincount(edges.ravel(),minlength=n);active=int((degrees>0).sum());m=edges.shape[1]
        # Yeni çiftler yalnız orijinal complement içinde ve nonzero-degree düğümler arasında olabilir.
        absent=active*(active-1)//2-m
        capacity=int(np.minimum(degrees[degrees>0],active-1-degrees[degrees>0]).sum()//2)
        upper=min(m,absent,capacity)/m if m else 0.
        rows.append({'context':row.context,'protocol':row.protocol,'threshold':row.threshold,
            'positive_degree_nodes':active,'undirected_edges':m,'changed_fraction':row.changed_fraction,
            'necessary_upper_bound_on_changed_fraction':upper,'bound_is_not_constructive_maximum':True,
            'raw_50pct_change_mathematically_excluded_by_bound':upper<.5,
            'null_status_original_policy':row.status})
    csv_write(QA/'shuffle_structural_limits.csv',pd.DataFrame(rows))
    cov=pd.read_csv(QA/'drug_ppi_coverage.csv')
    outer=cov[cov.inner_fold.eq(0)&cov.split.eq('test')]
    summary=outer.groupby(['protocol','threshold','role']).agg(
        test_drugs=('drug_id','nunique'),drugs_receiving_PPI=('has_any_PPI_message','sum'),
        drugs_with_linked_sequence=('linked_sequence_proteins',lambda s:int((s>0).sum())),
        query_unseen_self_only_relations=('query_unseen_self_only','sum')).reset_index()
    csv_write(QA/'outer_test_PPI_coverage_all62.csv',summary)
    original_path=ROOT/'configs/WP09_training_PROPOSED_v1.json'
    proposal=json.loads(original_path.read_text(encoding='utf-8'))
    revised=copy.deepcopy(proposal);revised['version']='WP09-training-PROPOSED-v2'
    revised['previous_proposal_sha256']=sha(original_path)
    revised['revision_basis']='label-independent topology and null feasibility only; no performance calculated or used'
    revised['threshold']['recommended_primary']=700
    revised['threshold']['sensitivities']=[400,900]
    revised['threshold']['reason']='400 coverage-first initial proposal has 0/40 accepted nulls; 700 has 39/40, retains same outer test drug any-role coverage as 400 in both protocols; 900 loses coverage'
    revised['null_failure_policy']='Keep NA_shuffle_insufficient; never retry seeds or lower 0.5 rule to turn observed failures into success; incomplete null comparison needs explicit approval'
    revised['open_gate'].append('accept explicit NA/null failure policy or authorize a separately versioned topology-only null rule; 700 has one failing inner context')
    target=ROOT/'configs/WP09_training_PROPOSED_v2.json'
    if target.exists() and json.loads(target.read_text(encoding='utf-8'))!=revised:raise RuntimeError('Do not silently revise proposal v2')
    json_write(target,revised)
    json_write(QA/'threshold_recommendation.json',{'recommended':700,'approved':None,
        'initial_proposed_400_kept_in_v1':True,'changed_reason_is_label_independent':True,
        'performance_not_computed':True,'threshold_claim':'coverage/null feasibility tradeoff, not optimal model threshold',
        'null_success_400':int(((quality.threshold==400)&quality.status.eq('OK_degree_preserving_null')).sum()),
        'null_success_700':int(((quality.threshold==700)&quality.status.eq('OK_degree_preserving_null')).sum()),
        'null_success_900':int(((quality.threshold==900)&quality.status.eq('OK_degree_preserving_null')).sum()),
        'training_enabled':False,'decision_gate':'separate user approval required'})
    print(pd.DataFrame(rows).groupby('threshold').agg(bound_min=('necessary_upper_bound_on_changed_fraction','min'),
        bound_max=('necessary_upper_bound_on_changed_fraction','max'),cannot_reach_half=('raw_50pct_change_mathematically_excluded_by_bound','sum')).to_string())
    print(summary[summary.role.eq('ALL')].to_string(index=False))


if __name__=='__main__':main()
