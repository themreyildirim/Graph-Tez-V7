"""Null v3 kapısı: model oluşturmadan koruma, replay ve ortak kapsam testleri."""
from pathlib import Path
import sys,json,hashlib,inspect,ast,copy,unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp09_null_gate import QA,DESIGN,CONFIG,preserve,common_scope,replay_trace
from wp09_shuffle import edge_hash


class NullGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=pd.read_csv(QA/'null_preflight_700_three_replicates.csv',keep_default_na=False)
        cls.old=pd.read_csv(DESIGN/'shuffle_quality.csv').query('threshold == 700')
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.diagnosis=json.loads((QA/'failure_diagnosis.json').read_text(encoding='utf-8'))

    def test_01_all_1567_prior_files_preserved(self):self.assertEqual(preserve(),1567)

    def test_02_input_and_policy_hashes_preserved(self):
        for name in ('input_manifest.json','schedule_input_manifest.json'):
            paths=json.loads((QA/name).read_text(encoding='utf-8'))
            self.assertEqual([],[p for p,h in paths.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h])
        policy=json.loads((QA/'policy_before_new_null_results.json').read_text(encoding='utf-8'))
        self.assertEqual(policy['configuration_sha256'],hashlib.sha256(CONFIG.read_bytes()).hexdigest())
        self.assertEqual(policy['generator_sha256'],hashlib.sha256((ROOT/'scripts/wp09_shuffle.py').read_bytes()).hexdigest())

    def test_03_old_replicate_zero_exactly_reproduced_all40(self):
        merged=self.rows[self.rows.replicate.eq(0)].merge(self.old,on='context',suffixes=('_new','_old'),validate='one_to_one')
        self.assertEqual(len(merged),40)
        for name in ('seed','status','shuffled_edge_sha256','changed_fraction','attempts','successful_swaps'):
            np.testing.assert_array_equal(merged[name+'_new'],merged[name+'_old'])

    def test_04_failure_is_endpoint_not_budget_exhaustion(self):
        d=self.diagnosis
        self.assertEqual((d['edges'],d['minimum_removed_for_50pct'],d['old_removed_original_edges']),(105,53,51))
        self.assertTrue(d['accepted_swap_target_met']);self.assertFalse(d['attempt_budget_exhausted'])
        self.assertEqual(d['old_attempts'],3801);self.assertEqual(d['budget'],21000)

    def test_05_trace_reintroduction_accounting_and_threshold_crossing(self):
        trace=pd.read_csv(QA/'failure_full_swap_trace.csv')
        np.testing.assert_array_equal(trace.original_edges_removed_cumulative-trace.original_edges_reintroduced_cumulative,trace.removed_original_edges)
        first=trace[trace.accepted_swaps.le(1050)]
        self.assertEqual(first.removed_original_edges.max(),63)
        self.assertEqual(first.iloc[-1].removed_original_edges,51)
        self.assertTrue((first.changed_fraction>=.5).any())
        endpoints=pd.read_csv(QA/'failure_fixed_horizon_diagnostics.csv')
        row=endpoints.iloc[0]
        self.assertEqual(row.attempts,row.accepted_swaps+row.shared_endpoint_rejections+row.existing_pair_rejections)

    def test_06_diagnostic_extended_endpoints_never_replace_old_failure(self):
        row=self.rows[self.rows.context.eq('stress_o02_i02')&self.rows.replicate.eq(0)].iloc[0]
        self.assertEqual(row.status,'NA_shuffle_insufficient');self.assertEqual(row.artifact_file,'')
        self.assertEqual(row.shuffled_edge_sha256,self.old[self.old.context.eq('stress_o02_i02')].iloc[0].shuffled_edge_sha256)
        self.assertTrue(self.diagnosis['extended_endpoint_not_used_as_replacement'])

    def test_07_all_fixed_seeds_no_best_replica_selection(self):
        for context,group in self.rows.groupby('context'):
            self.assertEqual(set(group.replicate),{0,1,2})
            base=int(self.old[self.old.context.eq(context)].iloc[0].seed)
            self.assertEqual(group.sort_values('replicate').seed.tolist(),[base,base+1000000,base+2000000])
        self.assertFalse(self.config['shuffle']['retry_or_best_replica_selection'])

    def test_08_successful_null_graph_invariants_all117(self):
        self.assertEqual(int(self.rows.status.eq('OK_degree_preserving_null').sum()),117)
        for row in self.rows.itertuples():
            if row.status!='OK_degree_preserving_null':
                self.assertEqual(row.artifact_file,'');continue
            path=ROOT/row.artifact_file
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row.artifact_sha256)
            with np.load(path,allow_pickle=False) as a:null=a['ppi_pairs']
            with np.load(DESIGN/'folds'/(row.context+'_train.npz'),allow_pickle=False) as a:real=a['ppi_pairs_700'];n=len(a['protein_ids'])
            self.assertEqual(real.shape,null.shape);self.assertTrue((null[0]<null[1]).all())
            self.assertEqual(len(set(map(tuple,null.T))),null.shape[1])
            np.testing.assert_array_equal(np.bincount(real.ravel(),minlength=n),np.bincount(null.ravel(),minlength=n))
            self.assertTrue(set(null.ravel())<=set(real.ravel()))
            self.assertEqual(edge_hash(map(tuple,null.T)),row.shuffled_edge_sha256)
            changed=len(set(map(tuple,real.T))-set(map(tuple,null.T)))/real.shape[1]
            self.assertAlmostEqual(changed,row.changed_fraction);self.assertGreaterEqual(changed,.5)

    def test_09_three_failures_in_two_inner_contexts_no_outer_replacement(self):
        failed=self.rows[self.rows.status.ne('OK_degree_preserving_null')]
        self.assertEqual(len(failed),3);self.assertTrue(failed.inner_fold.gt(0).all())
        self.assertEqual(set(failed.context),{'primary_o02_i01','stress_o02_i02'})
        self.assertEqual(len(list((QA/'nulls').glob('*.npz'))),117)

    def test_10_common_scope_exact_shared_two_fold_exclusions(self):
        result=common_scope(self.rows).set_index(['protocol','outer_fold'])
        self.assertEqual(result.loc[('primary',2),'common_valid_inner_folds'],'2,3')
        self.assertEqual(result.loc[('stress',2),'common_valid_inner_folds'],'1,3')
        self.assertTrue(result.common_valid_inner_count.ge(2).all());self.assertTrue(result.outer_all_three_nulls_valid.all())
        self.assertTrue(result.metric_evaluability_not_yet_tested.all())

    def test_11_minimum_two_is_enforced_no_success_zero(self):
        changed=self.rows.copy();changed.loc[changed.context.eq('primary_o02_i02')&changed.replicate.eq(0),'status']='NA_test'
        result=common_scope(changed).query("protocol == 'primary' and outer_fold == 2").iloc[0]
        self.assertEqual(result.common_valid_inner_count,1)
        self.assertEqual(result.topology_preflight_status,'NA_insufficient_common_inner')

    def test_12_any_outer_replica_failure_makes_whole_outer_primary_NA(self):
        changed=self.rows.copy();changed.loc[changed.context.eq('primary_o01_final')&changed.replicate.eq(1),'status']='NA_test'
        result=common_scope(changed).query("protocol == 'primary' and outer_fold == 1").iloc[0]
        self.assertEqual(result.topology_preflight_status,'NA_null_outer')
        self.assertFalse(result.training_authorized)

    def test_13_metric_NA_mask_common_only_no_metric_magnitude_argument(self):
        valid={c:True for c in self.rows.context.unique()};valid['primary_o01_i01']=False
        result=common_scope(self.rows,valid).query("protocol == 'primary' and outer_fold == 1").iloc[0]
        self.assertEqual(result.common_valid_inner_folds,'2,3');self.assertFalse(result.metric_evaluability_not_yet_tested)
        self.assertEqual(list(inspect.signature(common_scope).parameters),['rows','metric_valid'])

    def test_14_missing_or_duplicate_replica_is_rejected(self):
        with self.assertRaises(ValueError):common_scope(self.rows.iloc[1:])
        with self.assertRaises(ValueError):common_scope(pd.concat([self.rows,self.rows.iloc[:1]]))

    def test_15_preview_five_fits_identical_ID_target_scope_and_seed(self):
        preview=pd.read_csv(QA/'training_sequence_PREVIEW_ONLY.csv');self.assertEqual(len(preview),190)
        self.assertTrue(preview.status.eq('NOT_RUN_AWAITING_USER_APPROVAL').all())
        for context,group in preview.groupby('context'):
            self.assertEqual(len(group),5);self.assertEqual(group.identity_and_target_scope_sha256.nunique(),1)
            self.assertEqual(group.init_seed.nunique(),1);self.assertEqual(set(group.variant),{'G_noPPI','G_realPPI','G_shuffledPPI'})
        self.assertFalse(preview.context.isin(['primary_o02_i01','stress_o02_i02']).any())

    def test_16_preview_fit_IDs_and_targets_exact_frozen_sources(self):
        prep=ROOT/'reports/qa/WP08/experimental_preparation'
        parts=pd.read_csv(prep/'nested_partitions_v1.csv');vocab=json.loads((prep/'train_vocabularies.json').read_text(encoding='utf-8'))
        fit=json.loads((prep/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
        sources=json.loads((QA/'training_preview_sources.json').read_text(encoding='utf-8'))
        for context,source in sources.items():
            local=parts[parts.context.eq(context)]
            self.assertEqual(set(source['graph_train_ids']),set(local[local.split.eq('train')].drug_id))
            self.assertFalse(set(source['fit_eligible_train_ids'])&set(source['test_query_ids']))
            self.assertEqual(source['declared_train_B2_PT'],vocab[context]['B2']);self.assertEqual(source['fittable_train_B2_PT'],fit[context]['B2'])

    def test_17_v3_preserves_generator_and_700_training_gate_closed(self):
        c=self.config;self.assertFalse(c['training_enabled']);self.assertEqual(c['threshold']['recommended_primary'],700)
        self.assertIsNone(c['threshold']['approved_primary']);self.assertEqual(c['shuffle']['replicates'],3)
        self.assertEqual((c['shuffle']['swaps_per_edge'],c['shuffle']['attempts_per_edge'],c['shuffle']['minimum_changed_fraction']),(10,200,.5))
        self.assertEqual(c['previous_proposal_sha256'],hashlib.sha256((ROOT/'configs/WP09_training_PROPOSED_v2.json').read_bytes()).hexdigest())

    def test_18_no_model_optimizer_or_performance_execution(self):
        source=(ROOT/'scripts/wp09_null_gate.py').read_text(encoding='utf-8');tree=ast.parse(source)
        imported=[n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)]
        self.assertFalse(any(x.startswith(('torch','sklearn')) for x in imported))
        calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertFalse(set(calls)&{'fit','step','backward','zero_grad','predict','predict_proba'})
        done=json.loads((QA/'null_preflight_complete.json').read_text(encoding='utf-8'))
        self.assertFalse(done['training_or_optimizer_or_PT_scores'])


if __name__=='__main__':unittest.main(verbosity=2)
