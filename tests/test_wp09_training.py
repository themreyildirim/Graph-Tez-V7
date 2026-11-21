"""Gerçek v3 trainer/optimizer/heldout sınırı ve sabit OOF ablation doğrulaması."""
from pathlib import Path
import sys,json,copy,math,unittest
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp09_train import (QA,MODEL,PREP,NULL,SEMANTICS,NAMES,preserve,sha,source_labels,context_arguments,fit_model,
    restrict_labels,proxy_matrix,restore,load_bundle,select_query,state_hash,score_queries)
from wp09_train_evaluate import strict_mean3,bootstrap_primary
from wp08_baseline_metrics import MetricPanel,grouped_bootstrap_weights


class ActualTrainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.fit=pd.read_csv(QA/'model_fit_summary.csv');cls.pred=pd.read_csv(QA/'oof_predictions.csv')
        cls.source=source_labels();cls.jobs=pd.read_csv(NULL/'training_sequence_PREVIEW_ONLY.csv',keep_default_na=False)
        cls.metrics=pd.read_csv(QA/'metrics_with_group_CI.csv')
        cls.md=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(MODEL.glob('*.json'))]

    def test_01_all_accepted_files_and_model_artifact_hashes(self):
        self.assertEqual(preserve(),1711)
        for name in ('input_manifest.json','model_artifact_manifest.json'):
            expected=json.loads((QA/name).read_text(encoding='utf-8'))
            self.assertEqual([],[p for p,h in expected.items() if sha(ROOT/p)!=h])

    def test_02_real_optimizer_steps_and_updated_states_all190(self):
        self.assertEqual(len(self.fit),190);self.assertTrue(self.fit.status.eq('OK').all())
        self.assertTrue(self.fit.optimizer_steps.gt(0).all());self.assertGreater(int(self.fit.optimizer_steps.sum()),10000)
        self.assertTrue(self.fit.selected_state_L2_change.gt(0).all())
        self.assertTrue((self.fit.initial_state_sha256!=self.fit.selected_state_sha256).all())

    def test_03_PPI_message_gradients_reach_real_and_shuffled_not_noPPI(self):
        no=self.fit[self.fit.model.eq('G_noPPI')];ppi=self.fit[~self.fit.model.eq('G_noPPI')]
        self.assertTrue(no.maximum_message_gradient_norm.eq(0).all());self.assertTrue(no.maximum_train_message_input_norm.eq(0).all())
        self.assertTrue(ppi.maximum_message_gradient_norm.gt(0).all());self.assertTrue(ppi.maximum_train_message_input_norm.gt(0).all())

    def test_04_same_initial_weights_and_scope_for_each_five_fit_context(self):
        for context,group in self.fit.groupby('context'):
            self.assertEqual(len(group),5);self.assertEqual(group.initial_state_sha256.nunique(),1)
            models=[m for m in self.md if m['context']==context]
            self.assertEqual(len({json.dumps(m['fitted_targets']) for m in models}),1)
            self.assertEqual(len({json.dumps(m['train_fit_drug_ids']) for m in models}),1)

    def test_05_outer_epochs_exact_common_inner_median_no_test(self):
        decisions=json.loads((QA/'outer_fit_and_selection.json').read_text(encoding='utf-8'))
        for d in decisions:
            self.assertFalse(d['outer_test_labels_or_scores_used']);self.assertGreaterEqual(d['common_inner_count'],2)
            for model,epoch in d['outer_epoch_by_model'].items():
                f=self.fit[self.fit.protocol.eq(d['protocol'])&self.fit.outer_fold.eq(d['outer_fold'])&self.fit.model.eq(model)&self.fit.inner_fold.isin(d['actual_common_inner_folds'])]
                self.assertEqual(epoch,math.floor(float(np.median(f.best_epoch))+.5))
        commit=json.loads((QA/'selection_complete_before_test_scoring.json').read_text(encoding='utf-8'))
        self.assertFalse(commit['outer_test_scoring_performed'])
        self.assertTrue(all(sha(ROOT/p)==h for p,h in commit['selections'].items()))

    def test_06_exact_train_fit_ids_and_no_heldout_relations(self):
        parts=pd.read_csv(PREP/'nested_partitions_v1.csv');elig=pd.read_csv(PREP/'prediction_eligibility.csv')
        available=set(elig[elig.model.eq('B2')&elig.eligible].drug_id)
        for m in self.md:
            local=parts[parts.context.eq(m['context'])];train=set(local[local.split.eq('train')].drug_id)
            self.assertEqual(set(m['train_fit_drug_ids']),train&available)
            self.assertEqual(set(m['declared_graph_train_drug_ids']),train)
            self.assertFalse(set(m['train_fit_drug_ids'])&set(local[local.split.eq('test')].drug_id))
            self.assertFalse(set(m['validation_query_ids'])&set(local[local.split.eq('test')].drug_id))

    def test_07_frozen_fittable_PT_and_train_proxy_counts(self):
        fit=json.loads((PREP/'train_fittable_vocabularies_NO_model_fit.json').read_text(encoding='utf-8'))
        for m in self.md:
            self.assertEqual(m['fitted_targets'],fit[m['context']]['B2'])
            y=proxy_matrix(restrict_labels(self.source,m['train_fit_drug_ids']),m['train_fit_drug_ids'],m['fitted_targets'])
            self.assertEqual(m['train_observed_positive'],int(y.sum()))
            self.assertEqual(m['train_unknown_proxy_NOT_negative'],int(y.size-y.sum()))
            self.assertTrue(((y.sum(axis=0)>0)&(y.sum(axis=0)<len(y))).all())

    def test_08_saved_actual_parameters_reconstruct_outer_scores(self):
        for name in ('G_noPPI','G_realPPI','G_shuffledPPI_R0'):
            m=next(m for m in self.md if m['context']=='primary_o01_final' and m['model']==name)
            graph=load_bundle(m['context'],'train');query=load_bundle(m['context'],'query');null=None
            if m['null_file']:
                with np.load(ROOT/m['null_file'],allow_pickle=False) as a:null=a['ppi_pairs']
            query=select_query(query,list(query['drug_ids']),len(graph['protein_ids']))
            score=score_queries(m,graph,query,null)
            actual=self.pred[self.pred.protocol.eq('primary')&self.pred.outer_fold.eq(1)&self.pred.model.eq(name)]
            for i,d in enumerate(query['drug_ids']):
                if not query['eligible'][i]:continue
                expected=actual[actual.drug_id.eq(d)].set_index('class_id').loc[m['fitted_targets']].score_observed_record_proxy
                np.testing.assert_allclose(score[i],expected,rtol=1e-7,atol=1e-8)

    def test_09_actual_fixed_outer_fit_reproducibility(self):
        job=self.jobs[(self.jobs.context=='primary_o01_final')&(self.jobs.variant=='G_realPPI')].iloc[0].to_dict()
        md=next(m for m in self.md if m['context']==job['context'] and m['model']=='G_realPPI')
        g,q,t,n,v,y,yv,s=context_arguments(job,self.source)
        model,history,info=fit_model(g,y,t,job['variant'],job['init_seed'],n,fixed_epochs=md['best_epoch'])
        saved=restore(md).state_dict()
        for key,value in model.state_dict().items():torch.testing.assert_close(value,saved[key],rtol=1e-6,atol=1e-7)
        self.assertEqual(info['optimizer_steps'],md['optimizer_steps'])

    def test_10_real_trainer_heldout_label_and_value_mutation(self):
        job=self.jobs[(self.jobs.context=='primary_o01_i01')&(self.jobs.variant=='G_realPPI')].iloc[0].to_dict()
        args=context_arguments(job,self.source);g,q,t,n,v,y,yv,s=args
        held=set(s['test_query_ids']);mutated=self.source[~self.source.drug_id.isin(held)].copy()
        mutated=pd.concat([mutated,pd.DataFrame({'drug_id':list(held),'class_id':['MUTATED_OUTER_LABEL']*len(held)})])
        g2,q2,t2,n2,v2,y2,yv2,s2=context_arguments(job,mutated)
        altered={k:a.copy() for k,a in q2.items()};altered['chemistry'][altered['split']=='test']=1e9
        v2=select_query(altered,list(v2['drug_ids']),len(g2['protein_ids']))
        model,h,info=fit_model(g,y,t,job['variant'],job['init_seed'],n,v,yv,max_epochs=3)
        other,hh,ii=fit_model(g2,y2,t2,job['variant'],job['init_seed'],n2,v2,yv2,max_epochs=3)
        self.assertEqual(info['best_epoch'],ii['best_epoch'])
        np.testing.assert_allclose(h.validation_drug_AP,hh.validation_drug_AP,rtol=0,atol=1e-12)
        for key,value in model.state_dict().items():torch.testing.assert_close(value,other.state_dict()[key],rtol=0,atol=0)

    def test_11_trained_query_cannot_mutate_train_state_or_cache(self):
        md=next(m for m in self.md if m['context']=='primary_o01_final' and m['model']=='G_realPPI')
        model=restore(md);g=load_bundle(md['context'],'train');q=load_bundle(md['context'],'query')
        before=state_hash(model.state_dict())
        with torch.no_grad():
            cache=model.forward(g,700,'G_realPPI')['protein_h'].detach();saved=cache.clone()
            altered={k:a.copy() for k,a in q.items()};altered['chemistry'][altered['masks'][:,0]]+=100
            model.query_readout(q,cache);model.query_readout(altered,cache)
        self.assertEqual(before,state_hash(model.state_dict()));torch.testing.assert_close(cache,saved,rtol=0,atol=0)

    def test_12_trained_real_forward_uses_edges_noPPI_disables_them(self):
        g=load_bundle('primary_o01_final','train');empty={k:a.copy() for k,a in g.items()};empty['ppi_pairs_700']=np.empty((2,0),dtype=np.int64)
        for name in ('G_noPPI','G_realPPI'):
            md=next(m for m in self.md if m['context']=='primary_o01_final' and m['model']==name);model=restore(md)
            with torch.no_grad():a=model.forward(g,700,md['variant'])['protein_h'];b=model.forward(empty,700,md['variant'])['protein_h']
            if name=='G_noPPI':torch.testing.assert_close(a,b,rtol=0,atol=0)
            else:self.assertGreater(float((a-b).norm()),1e-5)

    def test_13_fixed_null_replicas_not_replaced_or_reselected(self):
        self.assertEqual(self.fit.groupby('model').size().to_dict(),{n:38 for n in NAMES})
        skipped=pd.read_csv(QA/'excluded_inner_jobs.csv');self.assertEqual(len(skipped),10)
        self.assertEqual(set(skipped.context),{'primary_o02_i01','stress_o02_i02'})
        for m in self.md:
            if m['variant']=='G_shuffledPPI':self.assertEqual(sha(ROOT/m['null_file']),m['null_file_sha256'])

    def test_14_equal_mean_of_three_metrics_not_prediction_ensemble(self):
        for (protocol,scope,metric),f in self.metrics.groupby(['protocol','scope','metric']):
            r=f[f.model.isin(['G_shuffledPPI_R0','G_shuffledPPI_R1','G_shuffledPPI_R2'])].estimate
            result=f[f.model.eq('G_shuffledPPI_mean3_metrics')].iloc[0].estimate
            self.assertAlmostEqual(float(np.mean(r)),result,places=12)
        self.assertNotIn('G_shuffledPPI_mean3_metrics',set(self.pred.model))
        self.assertTrue(np.isnan(strict_mean3([.5,.6,np.nan])))

    def test_15_exact_shared_baseline_keys_and_zero_exclusion(self):
        keys=pd.read_csv(QA/'comparison_keys.csv');excluded=pd.read_csv(QA/'excluded_comparison_keys.csv')
        self.assertTrue(excluded.empty)
        old=pd.read_csv(ROOT/'reports/qa/WP08/baseline_v1/oof_predictions.csv');old=old[old.family.eq('PT')]
        for protocol in ('primary','stress'):
            b2=old[old.protocol.eq(protocol)&old.model.eq('B2')][['outer_fold','drug_id','class_id']]
            b1=old[old.protocol.eq(protocol)&old.model.eq('B1')][['outer_fold','drug_id','class_id']]
            for scope,expected in [('own61',b2),('paired54',b2.merge(b1,on=['outer_fold','drug_id','class_id']))]:
                actual=keys[keys.protocol.eq(protocol)&keys.scope.eq(scope)]
                self.assertEqual(set(map(tuple,actual[['outer_fold','drug_id','class_id']].to_numpy())),set(map(tuple,expected.to_numpy())))

    def test_16_independent_sklearn_drug_AP_and_micro_AP(self):
        keys=pd.read_csv(QA/'comparison_keys.csv');keys=keys[keys.protocol.eq('primary')&keys.scope.eq('paired54')]
        actual=self.pred[self.pred.protocol.eq('primary')&self.pred.model.eq('G_realPPI')].merge(keys,on=['protocol','outer_fold','drug_id','class_id'])
        drug=[]
        for d,f in actual.groupby('drug_id'):
            if f.observed_record_s.nunique()==2:drug.append(average_precision_score(f.observed_record_s,f.score_observed_record_proxy))
        m=self.metrics[self.metrics.protocol.eq('primary')&self.metrics.scope.eq('paired54')&self.metrics.model.eq('G_realPPI')].set_index('metric').estimate
        self.assertAlmostEqual(float(np.mean(drug)),m['drug_macro_AP'],places=12)
        self.assertAlmostEqual(average_precision_score(actual.observed_record_s,actual.score_observed_record_proxy),m['micro_AP'],places=12)

    def test_17_structural_group_bootstrap_keeps_Levo_Oflox_and_NA(self):
        membership=pd.read_csv(PREP/'outer_membership_v1.csv');f=membership[membership.protocol.eq('primary')]
        ids=list(f.drug_id);group=dict(zip(ids,f.group_id));w=grouped_bootstrap_weights(ids,group,10,20270106)
        np.testing.assert_array_equal(w[:,ids.index('DB01137')],w[:,ids.index('DB01165')])
        panel=MetricPanel([[1,0],[0,1]],[[.9,.1],[.2,.8]],['a','b'],['X','Y'])
        result=bootstrap_primary(panel,np.array([[1.,0.],[0.,1.],[0.,0.]]))
        self.assertEqual(result['drug_macro_AP'][:2].tolist(),[1.,1.]);self.assertTrue(np.isnan(result['drug_macro_AP'][2]))

    def test_18_fold_AUROC_and_pooled_interpretation_separate(self):
        fold=pd.read_csv(QA/'outer_fold_metrics.csv')
        for protocol in ('primary','stress'):
            sub=fold[fold.protocol.eq(protocol)&fold.scope.eq('paired54')&fold.metric.eq('class_macro_AUROC')&fold.model.eq('B0_like_B2')]
            np.testing.assert_allclose(sub.estimate,.5)
        pooled=self.metrics[self.metrics.metric.eq('class_macro_AUROC')&self.metrics.model.eq('G_realPPI')]
        self.assertTrue(pooled.interpretation.eq('pooled diagnostic only').all())

    def test_19_all62_inventory_abstention_and_source_PT_preserved(self):
        status=pd.read_csv(QA/'prediction_status_all62.csv')
        self.assertEqual(len(status),620)
        self.assertTrue(status[status.drug_id.eq('DB06799')].status.eq('ABSTAIN_no_input').all())
        self.assertTrue(status[status.drug_id.eq('DB00684')].status.eq('SCORED').all())
        self.assertEqual((len(self.source),self.source.drug_id.nunique(),self.source.class_id.nunique()),(6416,62,1061))

    def test_20_actual_proxy_labels_match_source_for_every_OOF_pair(self):
        lookup={d:set(f.class_id) for d,f in self.source.groupby('drug_id')}
        expected=[int(c in lookup[d]) for d,c in zip(self.pred.drug_id,self.pred.class_id)]
        np.testing.assert_array_equal(self.pred.observed_record_s,expected)
        self.assertTrue(self.pred.semantics.str.contains('NOT verified biological negative',regex=False).all())

    def test_21_single_outcome_or_wrong_split_cannot_train_fallback(self):
        job=self.jobs[(self.jobs.context=='primary_o01_i01')&(self.jobs.variant=='G_realPPI')].iloc[0].to_dict()
        g,q,t,n,v,y,yv,s=context_arguments(job,self.source)
        bad={d:{'ALL'} for d in y}
        with self.assertRaises(ValueError):fit_model(g,bad,['ALL'],job['variant'],job['init_seed'],n,max_epochs=1,fixed_epochs=1)
        wrong={k:a.copy() for k,a in v.items()};wrong['split'][:]='test'
        with self.assertRaises(ValueError):fit_model(g,y,t,job['variant'],job['init_seed'],n,wrong,yv,max_epochs=1)
        with self.assertRaises(ValueError):proxy_matrix({**y,'HELDOUT':set()},list(y),t)

    def test_22_nonfinite_fit_is_recorded_NA_not_success(self):
        job=self.jobs[(self.jobs.context=='primary_o01_i01')&(self.jobs.variant=='G_realPPI')].iloc[0].to_dict()
        g,q,t,n,v,y,yv,s=context_arguments(job,self.source);g={k:a.copy() for k,a in g.items()};g['protein_x'][0,0]=np.nan
        model,history,info=fit_model(g,y,t,job['variant'],job['init_seed'],n,v,yv,max_epochs=1)
        self.assertEqual(info['status'],'NA_fit_exception');self.assertEqual(info['optimizer_steps'],0)

    def test_23_frozen_baseline_point_values_preserved(self):
        old=pd.read_csv(ROOT/'reports/qa/WP08/B0_frequency_reference_v1/metrics_with_group_CI.csv')
        for model in ('B1','B2','B0_like_B1','B0_like_B2','B0_all_train'):
            a=old[(old.protocol=='primary')&(old.scope=='paired54')&(old.model==model)&(old.metric=='drug_macro_AP')].iloc[0]
            b=self.metrics[(self.metrics.protocol=='primary')&(self.metrics.scope=='paired54')&(self.metrics.model==model)&(self.metrics.metric=='drug_macro_AP')].iloc[0]
            self.assertAlmostEqual(a.estimate,b.estimate,places=12)

    def test_24_coverage_counts_and_outside_positive_not_false_negative(self):
        c=pd.read_csv(QA/'evaluation_coverage.csv');sub=c[(c.protocol=='primary')&(c.scope=='paired54')]
        self.assertTrue(sub.scored_pairs.eq(13964).all());self.assertTrue(sub.observed_positive_scored.eq(3820).all())
        self.assertTrue(sub.unknown_NOT_verified_negative.eq(10144).all());self.assertTrue(sub.out_of_scored_vocab_positive.eq(1685).all())
        self.assertTrue(sub.class_AUROC_NA.gt(0).all())


if __name__=='__main__':unittest.main(verbosity=2)
