"""Keşifsel B0 için train-only sıklık, exact pairing ve koruma kontrolleri."""
from pathlib import Path
import sys,json,hashlib,inspect,re,unittest
import numpy as np
import pandas as pd
import nbformat
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp08_b0_frequency import QA,PREP,BASE,POLICY,frequency_estimate
from wp08_b0_evaluate import scoped_reference_rows
from wp08_baseline_metrics import RankingCache,grouped_bootstrap_weights


class B0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts=pd.read_csv(PREP/'nested_partitions_v1.csv');cls.elig=pd.read_csv(PREP/'prediction_eligibility.csv')
        cls.freq=pd.read_csv(QA/'train_frequency_estimates.csv');cls.population=pd.read_csv(QA/'train_population_ids.csv')
        cls.query=pd.read_csv(QA/'B0_outer_query_scores.csv');cls.pred=pd.read_csv(BASE/'oof_predictions.csv');cls.pred=cls.pred[cls.pred.family.eq('PT')]
        source=pd.read_csv(ROOT/'reports/qa/WP03/drug_pt_positives.csv');cls.source=source[source.conservative][['id','meddra_cui']].rename(columns={'id':'drug_id','meddra_cui':'pt_cui'})

    def test_01_old_outputs_models_and_inputs_unchanged(self):
        for filename in ('prior_outputs_hashes.json','input_manifest.json'):
            m=json.loads((QA/filename).read_text(encoding='utf-8'))
            self.assertTrue(m);self.assertEqual([],[p for p,h in m.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])

    def test_02_exploratory_policy_frozen_before_B0_result(self):
        policy=json.loads((QA/'policy_before_B0_results.json').read_text(encoding='utf-8'))
        self.assertEqual(policy,POLICY);self.assertTrue(policy['exploratory_after_B1_B2_results'])
        self.assertFalse(policy['hyperparameter_search']);self.assertIsNone(policy['smoothing'])
        self.assertEqual(policy['score_transform'],'identity')
        expected=json.loads((QA/'frequency_complete.json').read_text(encoding='utf-8'))['policy_sha256']
        self.assertEqual(hashlib.sha256((QA/'policy_before_B0_results.json').read_bytes()).hexdigest(),expected)

    def test_03_exact_train_populations_all_contexts(self):
        self.assertEqual(self.population.groupby(['context','reference']).ngroups,120)
        avail={m:set(self.elig[self.elig.model.eq(m)&self.elig.eligible].drug_id) for m in ('B1','B2')}
        for (context,ref),frame in self.population.groupby(['context','reference']):
            train=set(self.parts[self.parts.context.eq(context)&self.parts.split.eq('train')].drug_id)
            expected=train if ref=='B0_all_train' else train&avail[ref.removeprefix('B0_like_')]
            self.assertEqual(set(frame.train_drug_id),expected)

    def test_04_frequency_recomputed_from_unique_train_records(self):
        pops={k:set(f.train_drug_id) for k,f in self.population.groupby(['context','reference'])}
        for key,f in self.freq.groupby(['context','reference']):
            train=pops[key];count=self.source[self.source.drug_id.isin(train)].groupby('pt_cui').drug_id.nunique()
            expected=count.reindex(f.pt_cui,fill_value=0).to_numpy()
            np.testing.assert_array_equal(f.observed_train_drugs,expected)
            self.assertTrue(f.train_drugs.eq(len(train)).all())
            np.testing.assert_allclose(f.frequency_score,expected/len(train),rtol=0,atol=1e-15)

    def test_05_heldout_label_mutation_and_duplicate_ignored(self):
        observed=pd.DataFrame({'drug_id':['a','b','TEST'],'pt_cui':['X','Y','X']})
        before=frequency_estimate(observed,['a','b'],['X','Y','Z'])
        changed=pd.concat([observed.iloc[:2],pd.DataFrame({'drug_id':['TEST']*100,'pt_cui':['Z']*100})],ignore_index=True)
        pd.testing.assert_frame_equal(before,frequency_estimate(changed,['a','b'],['X','Y','Z']))
        self.assertEqual(before.frequency_score.tolist(),[.5,.5,0.])

    def test_06_estimator_rejects_biological_feature_columns(self):
        source=pd.DataFrame({'drug_id':['a'],'pt_cui':['X'],'MW':[100.]})
        with self.assertRaises(ValueError):frequency_estimate(source,['a'],['X'])
        self.assertEqual(list(inspect.signature(frequency_estimate).parameters),['observed','train_ids','targets'])
        for filename in ('wp08_b0_frequency.py','wp08_b0_evaluate.py'):
            text=(ROOT/'scripts'/filename).read_text(encoding='utf-8')
            self.assertNotRegex(text,r'\.fit\(');self.assertNotIn('LogisticRegression',text)

    def test_07_duplicate_train_records_and_empty_population_rejected(self):
        source=pd.DataFrame({'drug_id':['a','a'],'pt_cui':['X','X']})
        with self.assertRaises(ValueError):frequency_estimate(source,['a'],['X'])
        with self.assertRaises(ValueError):frequency_estimate(source,[],['X'])

    def test_08_frozen_target_dictionary_exact(self):
        vocab=json.loads((PREP/'train_vocabularies.json').read_text(encoding='utf-8'))
        for (context,ref),frame in self.freq.groupby(['context','reference']):
            self.assertEqual(set(frame.pt_cui),set(vocab[context]['cohort']))
            self.assertFalse(frame.pt_cui.duplicated().any())

    def test_09_query_scores_constant_for_drugs_in_same_fold(self):
        self.assertEqual(self.query.groupby(['protocol','outer_fold','reference','pt_cui']).frequency_score.nunique().max(),1)
        self.assertTrue(self.query.frequency_score.between(0,1).all())

    def test_10_Methenamine_population_reference_not_model_fallback(self):
        status=pd.read_csv(QA/'B0_status_all62.csv')
        for _,f in status.groupby(['protocol','reference']):self.assertEqual(f.drug_id.nunique(),62)
        meth=status[status.drug_id.eq('DB06799')]
        self.assertTrue(meth.status.eq('POPULATION_FREQUENCY_REFERENCE_NOT_PERSONALIZED').all())
        self.assertFalse(meth.biological_input_required.any())
        old=pd.read_csv(BASE/'prediction_status_all62.csv');self.assertTrue(old[old.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all())

    def test_11_matched_keys_identical_to_baselines(self):
        b0=pd.read_csv(QA/'B0_matched_scores.csv');complete=pd.read_csv(PREP/'complete_case_53_inventory_ONLY.csv')
        complete=set(complete[complete.complete_case_sensitivity].drug_id)
        for protocol in ('primary','stress'):
            for scope in ('own_B1','own_B2','paired54','complete_case53'):
                keys,_=scoped_reference_rows(self.pred,protocol,scope,complete)
                expected=set(keys.itertuples(index=False,name=None))
                for _,f in b0[b0.protocol.eq(protocol)&b0.scope.eq(scope)].groupby('model'):
                    self.assertEqual(set(f[['outer_fold','drug_id','class_id']].itertuples(index=False,name=None)),expected)

    def test_12_B1_B2_point_values_identical_to_accepted_run(self):
        old=pd.read_csv(BASE/'oof_metrics_with_group_CI.csv');new=pd.read_csv(QA/'metrics_with_group_CI.csv')
        for scope,original,model in [('own_B1','own','B1'),('own_B2','own','B2'),('paired54','paired54','B1'),('paired54','paired54','B2'),('complete_case53','complete_case53','B1'),('complete_case53','complete_case53','B2')]:
            left=new[new.scope.eq(scope)&new.model.eq(model)].sort_values(['protocol','metric'])
            right=old[old.family.eq('PT')&old.scope.eq(original)&old.model.eq(model)].sort_values(['protocol','metric'])
            np.testing.assert_allclose(left.estimate,right.estimate,rtol=0,atol=1e-12)

    def test_13_B0_class_AUROC_within_fold_is_tie_half(self):
        folds=pd.read_csv(QA/'within_outer_fold_metrics.csv')
        f=folds[folds.model.str.startswith('B0')&folds.metric.eq('class_macro_AUROC')]
        self.assertTrue(f['class_AUROC_evaluable'].gt(0).all())
        np.testing.assert_allclose(f.estimate,.5,rtol=0,atol=1e-15)
        ap,auc=RankingCache([1,0,1,0],[.7]*4,np.arange(4)).evaluate(np.ones(4))
        self.assertEqual(auc[0],.5);self.assertEqual(ap[0],.5)

    def test_14_group_draws_reproducible_and_keep_stereo_pair(self):
        outer=pd.read_csv(PREP/'outer_membership_v1.csv');outer=outer[outer.protocol.eq('primary')]
        ids=list(outer.drug_id);group=dict(zip(outer.drug_id,outer.group_id))
        a=grouped_bootstrap_weights(ids,group,50,20270106);b=grouped_bootstrap_weights(ids,group,50,20270106)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a[:,ids.index('DB01137')],a[:,ids.index('DB01165')])

    def test_15_coverage_equal_within_comparison(self):
        coverage=pd.read_csv(QA/'coverage_and_positive_unknown.csv')
        for (protocol,scope),f in coverage[coverage.scope.ne('B0_all62_reference_ONLY')].groupby(['protocol','scope']):
            for field in ('scored_drugs','scored_pairs','observed_positive_scored','unknown_scored_NOT_verified_negative'):
                self.assertEqual(f[field].nunique(),1)
        paired=coverage[coverage.protocol.eq('primary')&coverage.scope.eq('paired54')]
        self.assertTrue(paired.out_of_scored_vocab_positive.eq(1685).all())

    def test_16_difference_estimates_match_point_estimates(self):
        point=pd.read_csv(QA/'metrics_with_group_CI.csv');delta=pd.read_csv(QA/'paired_differences_group_CI.csv')
        lookup=point.set_index(['protocol','scope','model','metric']).estimate
        for r in delta.itertuples():
            self.assertAlmostEqual(r.first_minus_reference,lookup[r.protocol,r.scope,r.first,r.metric]-lookup[r.protocol,r.scope,r.reference,r.metric],places=12)

    def test_17_exploratory_CI_and_semantics_explicit(self):
        metrics=pd.read_csv(QA/'metrics_with_group_CI.csv');delta=pd.read_csv(QA/'paired_differences_group_CI.csv')
        self.assertTrue(metrics.exploratory_after_baseline.all());self.assertTrue(delta.exploratory_after_baseline.all())
        self.assertTrue(metrics.semantics.str.contains('NOT verified negative',regex=False).all())
        self.assertTrue(delta.CI_scope.str.contains('no full retraining',regex=False).all())
        self.assertTrue(metrics.valid_bootstrap_replicates.le(1000).all())

    def test_18_evaluation_did_not_change_estimates_or_C(self):
        done=json.loads((QA/'evaluation_complete.json').read_text(encoding='utf-8'))
        for file,key in [('train_frequency_estimates.csv','frequency_sha256_unchanged'),('B0_outer_query_scores.csv','query_scores_sha256_unchanged')]:
            self.assertEqual(hashlib.sha256((QA/file).read_bytes()).hexdigest(),done[key])
        self.assertEqual(hashlib.sha256((BASE/'selected_C.csv').read_bytes()).hexdigest(),done['selected_C_sha256_unchanged'])
        self.assertFalse(done['WP08_closed'] or done['WP09_started'])

    def test_19_executed_notebook_tables_and_figures(self):
        nb=nbformat.read(ROOT/'notebooks/WP08_B0_frequency_reference_v1.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertEqual([c.execution_count for c in code],list(range(1,8)))
        outputs=[o for c in code for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' or o.output_type=='stream' and o.name=='stderr' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data',{}) for o in outputs),5)
        fig=ROOT/'reports/figures/WP08/B0_frequency_reference_v1';self.assertEqual(len(list(fig.glob('*.png'))),5)


if __name__=='__main__':unittest.main(verbosity=2)
