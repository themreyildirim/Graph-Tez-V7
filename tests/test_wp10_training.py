"""Kaydedilmiş gerçek dört kollu fit/OOF ve factorial değerlendirme denetimi."""
import sys,json,math,copy,unittest
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp10_train as t
from wp10_molecular_encoder import initialized_model,model_digest
from wp10_training_forward import prepare,train_forward,query_forward


class ActualFactorialTrainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t.configure_runtime();cls.fit=pd.read_csv(t.QA/'model_fit_summary.csv');cls.pred=pd.read_csv(t.QA/'oof_predictions.csv')
        cls.md=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(t.MODEL.glob('*.json'))]
        cls.source=t.source_labels();cls.jobs=pd.read_csv(t.QA/'training_jobs_frozen.csv',keep_default_na=False)
        cls.metrics=pd.read_csv(t.QA/'metrics_with_group_CI.csv')

    def test_01_prior_artifacts_and_model_hashes_unchanged(self):
        self.assertGreaterEqual(t.preserve(),2487)
        for name in ['input_manifest.json','model_artifact_manifest.json','code_contract_before_fit.json']:
            expected=json.loads((t.QA/name).read_text(encoding='utf-8'));self.assertTrue(all(t.sha(ROOT/p)==h for p,h in expected.items()))

    def test_02_actual_optimizer_and_active_branch_gradients(self):
        self.assertEqual(len(self.fit),152);self.assertTrue(self.fit.status.eq('OK').all())
        self.assertTrue(self.fit.optimizer_steps.gt(0).all());self.assertTrue(self.fit.selected_state_L2_change.gt(0).all())
        for m in self.fit.itertuples():
            if m.model.startswith('A0'):
                self.assertEqual(m.maximum_atom_message_gradient_norm,0);self.assertEqual(m.molecular_state_L2_change,0)
            else:self.assertGreater(m.maximum_atom_message_gradient_norm,0);self.assertGreater(m.maximum_bond_message_gradient_norm,0)
            if m.model.endswith('0'):self.assertEqual(m.maximum_message_gradient_norm,0)
            else:self.assertGreater(m.maximum_message_gradient_norm,0)

    def test_03_all_four_same_init_scope_and_actual_parameter_count(self):
        for context,f in self.fit.groupby('context'):
            self.assertEqual(set(f.model),set(t.NAMES));self.assertEqual(f.initial_state_sha256.nunique(),1)
            local=[m for m in self.md if m['context']==context]
            self.assertEqual(len({json.dumps(m['fitted_targets']) for m in local}),1)
            self.assertEqual(len({json.dumps(m['train_fit_drug_ids']) for m in local}),1)
            for m in local:
                self.assertEqual(m['parameter_count'],5512+151*m['num_targets'])
                self.assertEqual(m['initial_state_sha256'],model_digest(initialized_model(m['seed'],num_targets=m['num_targets'])))

    def test_04_train_PT_support_and_fit_IDs(self):
        fittable=json.loads((t.PREP/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
        parts=pd.read_csv(t.PREP/'nested_partitions_v1.csv')
        for m in self.md:
            self.assertEqual(m['fitted_targets'],fittable[m['context']]['B2'])
            sub=parts[parts.context.eq(m['context'])];groups=dict(zip(sub.drug_id,sub.group_id));held=set(sub[~sub.split.eq('train')].drug_id)
            self.assertFalse(set(m['train_fit_drug_ids'])&held);self.assertFalse(set(m['train_molecule_ids'])&held)
            y=t.proxy_matrix(t.restrict_labels(self.source,m['train_fit_drug_ids']),m['train_fit_drug_ids'],m['fitted_targets'])
            self.assertEqual(int(y.sum()),m['train_observed_positive']);self.assertEqual(int(y.size-y.sum()),m['train_unknown_proxy_NOT_negative'])
            self.assertTrue((y.sum(0)>=5).all());self.assertTrue((y.sum(0)<len(y)).all())
            for j in range(y.shape[1]):self.assertGreaterEqual(len({groups[d] for d,v in zip(m['train_fit_drug_ids'],y[:,j]) if v}),2)

    def test_05_epoch_selection_only_common_inner_and_commits(self):
        decisions=json.loads((t.QA/'outer_fit_and_selection.json').read_text(encoding='utf-8'))
        for d in decisions:
            self.assertFalse(d['outer_test_labels_or_scores_used']);self.assertGreaterEqual(d['common_inner_count'],2)
            for arm,epochs in d['outer_epoch_by_model'].items():
                f=self.fit[self.fit.protocol.eq(d['protocol'])&self.fit.outer_fold.eq(d['outer_fold'])&self.fit.model.eq(arm)&self.fit.inner_fold.isin(d['actual_common_inner_folds'])]
                self.assertEqual(epochs,math.floor(float(np.median(f.best_epoch))+.5))
        commit=json.loads((t.QA/'selection_complete_before_test_scoring.json').read_text(encoding='utf-8'))
        self.assertFalse(commit['outer_test_scoring_performed']);self.assertTrue(all(t.sha(ROOT/p)==h for p,h in commit['selections'].items()))

    def test_06_npz_reconstruct_scores_all_four_against_reference_encoder(self):
        for arm in t.NAMES:
            md=next(m for m in self.md if m['context']=='primary_o01_final' and m['model']==arm)
            g=t.load_bundle(md['context'],'train');q=t.load_bundle(md['context'],'query')
            scores=t.score_queries(md,g,q);model=t.restore(md);store=t.get_store()
            with t.torch.no_grad():
                a=model.encode_train(g,store.make_batch(g['drug_ids']),arm)
                b=model.encode_query(g,q,store.make_batch(q['drug_ids']),a['cache'])
                expected=t.torch.sigmoid(b['logits']).numpy()
            np.testing.assert_allclose(scores,expected,rtol=1e-7,atol=1e-8,equal_nan=True)
            saved=self.pred[self.pred.protocol.eq('primary')&self.pred.outer_fold.eq(1)&self.pred.model.eq(arm)]
            for i,d in enumerate(q['drug_ids']):
                if not q['eligible'][i]:continue
                values=saved[saved.drug_id.eq(d)].set_index('class_id').loc[md['fitted_targets']].score_observed_record_proxy.to_numpy()
                np.testing.assert_allclose(scores[i],values,rtol=1e-7,atol=1e-8)

    def test_07_full_outer_fit_reproduction_no_model_files_written(self):
        job=self.jobs[self.jobs.context.eq('primary_o01_final')&self.jobs.variant.eq('A1P1')].iloc[0].to_dict()
        md=next(m for m in self.md if m['context']==job['context'] and m['model']=='A1P1')
        g,q,k,n,v,y,yv,s=t.context_arguments(job,self.source)
        model,h,info=t.fit_model(g,y,k,'A1P1',job['init_seed'],fixed_epochs=md['best_epoch'])
        self.assertEqual(info['selected_state_sha256'],md['selected_state_sha256'])
        self.assertEqual(info['optimizer_steps'],md['optimizer_steps'])

    def test_08_trained_query_value_mutation_cache_and_state_isolation(self):
        md=next(m for m in self.md if m['context']=='primary_o01_final' and m['model']=='A1P1')
        model=t.restore(md);g=t.load_bundle(md['context'],'train');q=t.load_bundle(md['context'],'query');store=t.get_store()
        ti=prepare(model,g,store.make_batch(g['drug_ids']));qi=prepare(model,q,store.make_batch(q['drug_ids']))
        before=t.state_hash(model.state_dict())
        with t.torch.no_grad():
            cache=train_forward(model,ti,'A1P1')['protein_h'];saved=cache.clone();a=query_forward(model,qi,cache,'A1P1')['logits']
            altered={k:v.copy() for k,v in q.items()};i=int(np.flatnonzero(q['masks'][:,0])[0]);altered['chemistry'][i]+=100
            b=query_forward(model,prepare(model,altered,store.make_batch(q['drug_ids'])),cache,'A1P1')['logits']
        keep=np.arange(len(q['drug_ids']))!=i
        t.torch.testing.assert_close(a[keep],b[keep],rtol=0,atol=0,equal_nan=True)
        t.torch.testing.assert_close(cache,saved,rtol=0,atol=0);self.assertEqual(before,t.state_hash(model.state_dict()))

    def test_09_shared_comparison_keys_exactly_frozen(self):
        keys=pd.read_csv(t.QA/'comparison_keys.csv');self.assertTrue(pd.read_csv(t.QA/'excluded_comparison_keys.csv').empty)
        old=pd.read_csv(ROOT/'reports/qa/WP09/training_v1/comparison_keys.csv')
        columns=['protocol','scope','outer_fold','drug_id','class_id']
        self.assertEqual(set(map(tuple,keys[columns].to_numpy())),set(map(tuple,old[columns].to_numpy())))
        for protocol,f in self.pred.groupby('protocol'):
            keysets=[set(map(tuple,g[['outer_fold','drug_id','class_id']].to_numpy())) for _,g in f.groupby('model')]
            self.assertTrue(all(k==keysets[0] for k in keysets))

    def test_10_independent_AP_and_source_proxy_truth(self):
        keys=pd.read_csv(t.QA/'comparison_keys.csv');keys=keys[keys.protocol.eq('primary')&keys.scope.eq('paired54')]
        truth={d:set(f.class_id) for d,f in self.source.groupby('drug_id')}
        self.assertTrue(all(int(c in truth[d])==s for d,c,s in zip(self.pred.drug_id,self.pred.class_id,self.pred.observed_record_s)))
        for arm in t.NAMES:
            f=self.pred[self.pred.protocol.eq('primary')&self.pred.model.eq(arm)].merge(keys,on=['protocol','outer_fold','drug_id','class_id'])
            value=np.mean([average_precision_score(g.observed_record_s,g.score_observed_record_proxy) for _,g in f.groupby('drug_id') if g.observed_record_s.nunique()==2])
            expected=self.metrics[self.metrics.protocol.eq('primary')&self.metrics.scope.eq('paired54')&self.metrics.model.eq(arm)&self.metrics.metric.eq('drug_macro_AP')].iloc[0].estimate
            self.assertAlmostEqual(value,expected,places=12)

    def test_11_factorial_contrasts_exact_arithmetic_and_group_draws(self):
        contrasts=pd.read_csv(t.QA/'factorial_contrasts_group_CI.csv')
        for r in contrasts.itertuples():
            f=self.metrics[self.metrics.protocol.eq(r.protocol)&self.metrics.scope.eq(r.scope)&self.metrics.metric.eq(r.metric)].set_index('model').estimate
            coeff=json.loads(r.coefficients);self.assertAlmostEqual(r.estimate,sum(c*f[name] for name,c in coeff.items()),places=12)
            self.assertEqual(r.valid_bootstrap_replicates,1000)
        from wp08_baseline_metrics import grouped_bootstrap_weights
        membership=pd.read_csv(t.PREP/'outer_membership_v1.csv');f=membership[membership.protocol.eq('primary')];ids=list(f.drug_id)
        weights=grouped_bootstrap_weights(ids,dict(zip(f.drug_id,f.group_id)),10,20270106)
        np.testing.assert_array_equal(weights[:,ids.index('DB01137')],weights[:,ids.index('DB01165')])

    def test_12_scope_unknown_abstention_and_no_null_experiments(self):
        status=pd.read_csv(t.QA/'prediction_status_all62.csv');self.assertEqual(len(status),496)
        self.assertTrue(status[status.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all())
        self.assertTrue(status[status.drug_id.eq('DB00684')].status.eq('SCORED').all())
        c=pd.read_csv(t.QA/'evaluation_coverage.csv');c=c[c.protocol.eq('primary')&c.scope.eq('paired54')]
        self.assertTrue(c.out_of_scored_vocab_positive.eq(1685).all());self.assertTrue(c.unknown_NOT_verified_negative.eq(10144).all())
        self.assertEqual((len(self.source),self.source.drug_id.nunique(),self.source.class_id.nunique()),(6416,62,1061))
        self.assertEqual(set(self.pred.model),set(t.NAMES))

    def test_13_references_and_class_AUROC_interpretation_preserved(self):
        old=pd.read_csv(ROOT/'reports/qa/WP09/training_v1/metrics_with_group_CI.csv')
        for name in ['B1','B2','B0_like_B2']:
            a=old[old.protocol.eq('primary')&old.scope.eq('paired54')&old.model.eq(name)&old.metric.eq('drug_macro_AP')].iloc[0].estimate
            b=self.metrics[self.metrics.protocol.eq('primary')&self.metrics.scope.eq('paired54')&self.metrics.model.eq(name)&self.metrics.metric.eq('drug_macro_AP')].iloc[0].estimate
            self.assertAlmostEqual(a,b,places=12)
        self.assertTrue(self.metrics[self.metrics.metric.eq('class_macro_AUROC')].interpretation.eq('pooled diagnostic only').all())


if __name__=='__main__':unittest.main(verbosity=2)
