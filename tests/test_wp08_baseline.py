"""Onaylı WP08 LR ve observed-record proxy değerlendirme sınırları."""
from pathlib import Path
import sys,json,hashlib,unittest
import numpy as np
import pandas as pd
import nbformat
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp08_baseline_train import (QA,PREP,MODEL,GRID,SEED,positive_lookup,proxy_matrix,fit_binary_models,
                                predict_parameters,tune_fold,choose_C,load_labels)
from wp08_baseline_metrics import (RankingCache,MetricPanel,grouped_bootstrap_weights,percentile_interval,METRICS)
from sklearn.metrics import average_precision_score,roc_auc_score


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts=pd.read_csv(PREP/'nested_partitions_v1.csv');cls.elig=pd.read_csv(PREP/'prediction_eligibility.csv')
        cls.selected=pd.read_csv(QA/'selected_C.csv');cls.pred=pd.read_csv(QA/'oof_predictions.csv')
        cls.labels=load_labels();cls.config=json.loads((QA/'run_config.json').read_text(encoding='utf-8'))

    def test_01_all_prior_and_preparation_hashes(self):
        for name in ('prior_outputs_hashes.json','preparation_input_manifest.json','model_artifact_manifest.json'):
            m=json.loads((QA/name).read_text(encoding='utf-8'))
            self.assertTrue(m);self.assertEqual([],[p for p,h in m.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])

    def test_02_actual_locked_split_hash(self):
        frozen=json.loads((PREP/'frozen_split_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(frozen,self.config['split_manifest'])
        for p,h in frozen.items():self.assertEqual(hashlib.sha256((PREP/p).read_bytes()).hexdigest(),h)
        self.assertEqual(SEED,20261106)

    def test_03_C_selection_recomputed_inner_only(self):
        trace=pd.read_csv(QA/'inner_selection_metrics.csv')
        for row in self.selected.itertuples():
            f=trace[trace.protocol.eq(row.protocol)&trace.outer_fold.eq(row.outer_fold)&trace.family.eq(row.family)&trace.model.eq(row.model)]
            piv=f.pivot(index='inner_fold',columns='C',values='drug_macro_AP')
            choice,means,valid=choose_C({c:piv[c].to_numpy() for c in GRID})
            self.assertEqual(choice,row.selected_C);self.assertEqual(valid,row.valid_inner_folds)
            self.assertEqual(f.groupby('inner_fold').scope_hash.nunique().max(),1)

    def test_04_C_tie_smaller_and_NA_not_zero(self):
        chosen,means,valid=choose_C({.1:[.5,np.nan,.6],1.:[.5,np.nan,.6],10.:[.4,np.nan,.5]})
        self.assertEqual(chosen,.1);self.assertEqual(valid,2);self.assertAlmostEqual(means[.1],.55)
        self.assertIsNone(choose_C({c:[np.nan]*3 for c in GRID})[0])

    def test_05_every_model_exact_train_fit_ids(self):
        fit_sources=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text(encoding='utf-8'))
        self.assertEqual(len(list(MODEL.glob('*.json'))),400)
        for path in MODEL.glob('*.json'):
            md=json.loads(path.read_text(encoding='utf-8'));context=md['context'];model=md['baseline']
            train=set(self.parts[self.parts.context.eq(context)&self.parts.split.eq('train')].drug_id)
            available=set(self.elig[self.elig.model.eq(model)&self.elig.eligible].drug_id)
            self.assertEqual(set(md['train_drug_ids']),train&available)
            self.assertEqual(md['transform_fit_sources'],fit_sources[context])
            self.assertFalse(md['graph_has_PPI'])

    def test_06_outer_model_C_matches_selected(self):
        for r in self.selected.itertuples():
            md=json.loads((MODEL/f'{r.protocol}_o{r.outer_fold:02}_final_{r.family}_{r.model}_selected.json').read_text(encoding='utf-8'))
            self.assertEqual(md['C'],r.selected_C)
            self.assertEqual(md['selected_C_trace']['selected_C'],r.selected_C)

    def test_07_heldout_drug_never_outer_training(self):
        for r in self.pred[['protocol','outer_fold','family','model','drug_id']].drop_duplicates().itertuples():
            ctx=f'{r.protocol}_o{r.outer_fold:02}_final'
            sub=self.parts[self.parts.context.eq(ctx)]
            self.assertIn(r.drug_id,set(sub[sub.split.eq('test')].drug_id))
            self.assertNotIn(r.drug_id,set(sub[sub.split.eq('train')].drug_id))

    def test_08_frozen_PT_dictionary_respected(self):
        voc=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
        for (protocol,fold,model),f in self.pred[self.pred.family.eq('PT')].groupby(['protocol','outer_fold','model']):
            self.assertTrue(set(f.class_id)<=set(voc[f'{protocol}_o{fold:02}_final'][model]))

    def test_09_no_one_proxy_class_fit_or_fallback(self):
        X=np.arange(12).reshape(6,2);ids=[f'D{i}' for i in range(6)]
        params,trace=fit_binary_models(X,ids,['all','none'],{'all':set(ids),'none':set()},.1)
        self.assertEqual(params,{})
        self.assertEqual({r['status'] for r in trace},{'NA_single_proxy_outcome'})
        self.assertTrue(np.isnan(predict_parameters(X,params,['all','none'])).all())

    def test_10_heldout_labels_and_values_do_not_change_inner_C(self):
        context='primary_o01_i01';sub=self.parts[self.parts.context.eq(context)]
        available=set(self.elig[self.elig.model.eq('B1')&self.elig.eligible].drug_id)
        train=set(sub[sub.split.eq('train')].drug_id)&available;val=set(sub[sub.split.eq('validation')].drug_id)&available
        held=set(sub[sub.split.eq('test')].drug_id)
        lookup=positive_lookup(self.labels['PT']);targets=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))[context]['B1'][:3]
        with np.load(PREP/'features'/(context+'.npz'),allow_pickle=False) as a:ids=list(a['drug_ids']);X=a['B1'].copy()
        _,_,before,_=tune_fold(X,ids,train,val,targets,lookup)
        mutation={c:(set(v)-held) for c,v in lookup.items()}
        changed=X.copy();changed[[ids.index(d) for d in held]]=1e12
        _,_,after,_=tune_fold(changed,ids,train,val,targets,mutation)
        self.assertEqual(before,after)

    def test_11_training_parameters_ignore_all_nontrain_labels(self):
        X=np.array([[0.,1.],[1.,0.],[2.,1.],[3.,0.]])
        ids=['a','b','c','d'];lookup={'x':{'a','b','TEST'}}
        p,_=fit_binary_models(X,ids,['x'],lookup,.1)
        q,_=fit_binary_models(X,ids,['x'],{'x':{'a','b'}},.1)
        np.testing.assert_array_equal(p['x'][0],q['x'][0]);self.assertEqual(p['x'][1],q['x'][1])

    def test_12_real_component_fit_reproducibility(self):
        md=json.loads((MODEL/'primary_o01_final_PT_B1_selected.json').read_text(encoding='utf-8'))
        target=md['fitted_classes'][0]
        with np.load(PREP/'features/primary_o01_final.npz',allow_pickle=False) as a:
            ids=list(a['drug_ids']);X=a['B1'][[ids.index(d) for d in md['train_drug_ids']]]
        p,_=fit_binary_models(X,md['train_drug_ids'],[target],positive_lookup(self.labels['PT']),md['C'])
        with np.load(ROOT/md['parameters_file'],allow_pickle=False) as saved:
            j=list(saved['class_ids']).index(target)
            np.testing.assert_allclose(p[target][0],saved['coef'][j],rtol=0,atol=1e-12)
            self.assertAlmostEqual(p[target][1],saved['intercept'][j],places=12)

    def test_13_outer_scores_reconstructed_from_parameters(self):
        for model in ('B1','B2'):
            md=json.loads((MODEL/f'primary_o01_final_PT_{model}_selected.json').read_text(encoding='utf-8'))
            with np.load(ROOT/md['parameters_file'],allow_pickle=False) as saved:
                targets=list(saved['class_ids']);params={c:(saved['coef'][j],saved['intercept'][j]) for j,c in enumerate(targets)}
            selected=self.pred[self.pred.protocol.eq('primary')&self.pred.outer_fold.eq(1)&self.pred.family.eq('PT')&self.pred.model.eq(model)]
            drugs=sorted(selected.drug_id.unique())
            with np.load(PREP/'features/primary_o01_final.npz',allow_pickle=False) as a:
                ids=list(a['drug_ids']);X=a[model][[ids.index(d) for d in drugs]]
            scores=predict_parameters(X,params,targets)
            actual=selected.pivot(index='drug_id',columns='class_id',values='score_observed_record_proxy').loc[drugs,targets]
            np.testing.assert_allclose(scores,actual,rtol=1e-12,atol=1e-12)

    def test_14_abstention_and_62_inventory(self):
        status=pd.read_csv(QA/'prediction_status_all62.csv')
        self.assertEqual(len(status),2*2*2*62)
        self.assertTrue(status[status.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all())
        self.assertNotIn('DB06799',set(self.pred.drug_id))
        for _,f in status.groupby(['protocol','family','model']):self.assertEqual(f.drug_id.nunique(),62)

    def test_15_proxy_labels_exactly_source_records(self):
        for family,frame in self.pred.groupby('family'):
            lookup=positive_lookup(self.labels[family])
            expected=[int(r.drug_id in lookup.get(r.class_id,set())) for r in frame.itertuples()]
            np.testing.assert_array_equal(frame.observed_record_s,expected)
            self.assertTrue(frame.score_observed_record_proxy.between(0,1).all())

    def test_16_weighted_metrics_match_sklearn_with_ties(self):
        rng=np.random.default_rng(7)
        for _ in range(20):
            y=rng.integers(0,2,size=20);scores=rng.integers(0,5,size=20)/5;w=rng.integers(0,4,size=20)
            if not (w[y==0].sum()>0 and w[y==1].sum()>0):continue
            ap,auc=RankingCache(y,scores,np.arange(20)).evaluate(w)
            self.assertAlmostEqual(ap[0],average_precision_score(y,scores,sample_weight=w),places=12)
            self.assertAlmostEqual(auc[0],roc_auc_score(y,scores,sample_weight=w),places=12)

    def test_17_AP_is_not_trapezoid_and_unknown_NA(self):
        y=np.array([0,1,0,1]);s=np.array([.9,.8,.7,.6])
        ap,_=RankingCache(y,s,np.arange(4)).evaluate(np.ones(4))
        self.assertAlmostEqual(ap[0],(1/2+2/4)/2)
        for labels in ([0,0],[1,1]):
            a,u=RankingCache(labels,[.1,.9],[0,1]).evaluate([1,1]);self.assertTrue(np.isnan(a[0]));self.assertTrue(np.isnan(u[0]))

    def test_18_group_bootstrap_keeps_members_and_seed(self):
        ids=['a','b','c'];groups={'a':'G','b':'G','c':'H'}
        a=grouped_bootstrap_weights(ids,groups,100,SEED);b=grouped_bootstrap_weights(ids,groups,100,SEED)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a[:,0],a[:,1])
        self.assertTrue((a[:,0]+a[:,2]==2).all())
        primary=pd.read_csv(PREP/'outer_membership_v1.csv');primary=primary[primary.protocol.eq('primary')]
        group=dict(zip(primary.drug_id,primary.group_id));ids=list(primary.drug_id)
        w=grouped_bootstrap_weights(ids,group,10,SEED)
        np.testing.assert_array_equal(w[:,ids.index('DB01137')],w[:,ids.index('DB01165')])

    def test_19_bootstrap_NA_reason_instead_of_zero(self):
        lo,hi,valid,reason=percentile_interval([np.nan]*20,min_valid=10)
        self.assertIsNone(lo);self.assertIsNone(hi);self.assertEqual(valid,0);self.assertTrue(reason)

    def test_20_paired_same_drugs_targets(self):
        from wp08_baseline_evaluate import make_panels
        outer=pd.read_csv(PREP/'outer_membership_v1.csv');vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
        hist=json.loads((PREP/'historical30_reference.json').read_text(encoding='utf-8'))['classes']
        for scope,n in [('paired54',54),('complete_case53',53)]:
            panels,_=make_panels('primary','PT',self.pred,outer,self.elig,vocab,hist,scope)
            np.testing.assert_array_equal(panels['B1'].mask,panels['B2'].mask)
            self.assertEqual(panels['B1'].classes,panels['B2'].classes)
            self.assertEqual(int(panels['B1'].mask.any(axis=1).sum()),n)

    def test_21_metrics_support_and_pair_counts(self):
        c=pd.read_csv(QA/'evaluation_coverage.csv')
        self.assertTrue((c.observed_positive_scored+c.unknown_scored_NOT_verified_negative==c.scored_pairs).all())
        self.assertTrue((c.observed_positive_scored+c.out_of_scored_vocab_positive==c.source_positive_for_scored_drugs).all())
        self.assertEqual(set(c.family),{'PT','historical30'})

    def test_22_point_metrics_independent_sklearn_recalculation(self):
        f=self.pred[self.pred.protocol.eq('primary')&self.pred.family.eq('PT')&self.pred.model.eq('B1')]
        aps=[]
        for drug,sub in f.groupby('drug_id'):
            if sub.observed_record_s.nunique()==2:aps.append(average_precision_score(sub.observed_record_s,sub.score_observed_record_proxy))
        reported=pd.read_csv(QA/'oof_metrics_with_group_CI.csv')
        r=reported[reported.protocol.eq('primary')&reported.family.eq('PT')&reported.model.eq('B1')&reported.scope.eq('own')&reported.metric.eq('drug_macro_AP')].iloc[0]
        self.assertAlmostEqual(r.estimate,float(np.mean(aps)),places=12)

    def test_23_CI_replicates_and_semantics_explicit(self):
        m=pd.read_csv(QA/'oof_metrics_with_group_CI.csv');d=pd.read_csv(QA/'paired_B2_minus_B1_group_CI.csv')
        self.assertEqual(len(m),2*2*3*2*len(METRICS))
        self.assertTrue((m.valid_bootstrap_replicates<=1000).all())
        self.assertTrue(m.semantics.str.contains('NOT a verified biological negative',regex=False).all())
        self.assertTrue(d.CI_interpretation.str.contains('not full retraining',regex=False).all())

    def test_24_class_NA_has_support_reason(self):
        c=pd.read_csv(QA/'per_class_metrics.csv');invalid=c.AUROC.isna()
        self.assertTrue(c.loc[invalid,'NA_reason'].notna().all())
        self.assertTrue(((c.loc[invalid,'observed_positive']==0)|(c.loc[invalid,'unobserved_NOT_verified_negative']==0)).all())
        folds=pd.read_csv(QA/'outer_fold_metrics.csv');self.assertTrue(folds.CI_NA_reason.notna().all())

    def test_25_historical30_separate_no_added_variants(self):
        self.assertTrue(set(self.pred[self.pred.family.eq('historical30')].class_id)<=set(json.loads((PREP/'historical30_reference.json').read_text(encoding='utf-8'))['classes']))
        self.assertFalse(self.config['ATC'] or self.config['RF_MLP'] or self.config['PPI'] or self.config['context80'] or self.config['WP09'])

    def test_26_selection_commit_before_outer_scoring_is_immutable(self):
        commit=json.loads((QA/'selection_complete_before_outer_scoring.json').read_text(encoding='utf-8'))
        self.assertFalse(commit['outer_test_scoring_performed'])
        self.assertEqual(hashlib.sha256((QA/'selected_C.csv').read_bytes()).hexdigest(),commit['selected_C_sha256'])
        evaluation=json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))
        self.assertEqual(evaluation['selected_C_sha256_unchanged'],commit['selected_C_sha256'])

    def test_27_expected_model_and_source_semantic_fields(self):
        md=json.loads((MODEL/'primary_o01_final_PT_B1_selected.json').read_text(encoding='utf-8'))
        for key in ['split_manifest','C','seed','feature_schema','transform_fit_sources','declared_target_dictionary','model_version','semantics']:
            self.assertIn(key,md)
        with np.load(ROOT/md['parameters_file'],allow_pickle=False) as a:self.assertIn('semantics',a.files)

    def test_28_notebook_executed_and_scientific_figures(self):
        nb=nbformat.read(ROOT/'notebooks/WP08_baseline_results.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertEqual([c.execution_count for c in code],list(range(1,9)))
        out=[o for c in code for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in out))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in out),6)
        fig=ROOT/'reports/figures/WP08/baseline_v1';self.assertEqual(len(list(fig.glob('*.png'))),6)


if __name__=='__main__':unittest.main(verbosity=2)
