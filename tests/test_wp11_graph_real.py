"""Gerçek kayıtlı A1P1: salt okunur attribution ve izolasyon testleri."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp11_graph_policy import ROOT,QA,ROLES,preserve,verify
from wp11_graph_run import load,forward,stability_probe,old
from wp11_graph_forward import cache_for,resolve_relation,pair_index_by_ids,torch,numeric_digest,protein_messages


class RealGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
        cls.s=load('primary_o01_final');cls.summary=pd.read_csv(QA/'intervention_summary.csv');cls.coverage=pd.read_csv(QA/'drug_coverage.csv')

    def test_01_policy_and_source_hashes(self):
        self.assertEqual(verify('policy_commit_before_attribution.json'),6);self.assertGreater(verify('input_manifest.json'),100)

    def test_02_all_accepted_artifacts_including_B1(self):self.assertEqual(preserve(),3079)

    def test_03_synthetic_gate_preceded_real_attribution(self):
        gate=json.loads((QA/'synthetic_gate_PASS.json').read_text());start=json.loads((QA/'real_attribution_started.json').read_text())
        self.assertEqual(gate['tests'],10);self.assertLess(gate['gate_time_ns'],start['time_ns'])

    def test_04_all10_reference_and_OOF_reconstruction(self):
        df=pd.read_csv(QA/'consistency_checks.csv');self.assertEqual(len(df),10)
        self.assertTrue(df.model_graph_query_cache_unchanged.all());self.assertLessEqual(df.reference_logit_error.max(),1e-5);self.assertLessEqual(df.original_cache_error.max(),1e-5);self.assertLessEqual(df.OOF_score_error.max(),1e-7)

    def test_05_real_role_mask_analytic_head_delta(self):
        s=self.s;m=s['model'];q=s['q'];pool=torch.cat([s['cache'].protein_h,s['unseen']]);g=s['g']
        with torch.no_grad():
            base=forward(s)['logits']
            for ri,r in enumerate(ROLES):
                e=q['role_'+r]
                if e.shape[1]==0:continue
                d,p=map(int,e[:,0]);n=int((e[0]==d).sum());actual=base[d]-forward(s,relation=(r,d,p))['logits'][d]
                expected=m.head.weight[:,8+32*ri:8+32*(ri+1)]@(pool[p]/n)
                torch.testing.assert_close(actual,expected,rtol=0,atol=1e-5)

    def test_06_real_query_model_graph_cache_immutable(self):
        s=self.s;before=numeric_digest({'g':numeric_digest(s['g']),'q':numeric_digest(s['q']),'m':numeric_digest(s['model'].state_dict()),'h':s['cache'].protein_h})
        q=s['q'];r=next(r for r in ROLES if q['role_'+r].shape[1]);d,p=map(int,q['role_'+r][:,0])
        with torch.no_grad():
            original=forward(s)['logits'];alt=forward(s,relation=(r,d,p))['logits'];cache=cache_for(s['model'],s['g'],0);forward(s,cache=cache)
        others=[i for i in range(len(q['drug_ids'])) if i!=d]
        torch.testing.assert_close(original[others],alt[others],rtol=0,atol=0,equal_nan=True)
        self.assertEqual(before,numeric_digest({'g':numeric_digest(s['g']),'q':numeric_digest(s['q']),'m':numeric_digest(s['model'].state_dict()),'h':s['cache'].protein_h}))
        self.assertIsNot(cache.protein_h,s['cache'].protein_h)

    def test_07_actual_ID_resolution_and_two_way_mask(self):
        s=self.s;g=s['g'];a,b=g['protein_ids'][g['ppi_pairs_700'][:,0]]
        self.assertEqual(pair_index_by_ids(g,a,b),pair_index_by_ids(g,b,a))
        with torch.no_grad():out=protein_messages(s['model'].base.protein,torch.tensor(g['protein_x'],dtype=torch.float32),g['ppi_pairs_700'],0)
        self.assertEqual(int((out['weights']==0).sum()),2)

    def test_08_all62_inventory61eligible_and_NA_preserved(self):
        for p in ['primary','stress']:
            df=self.coverage[self.coverage.protocol.eq(p)];self.assertEqual(df.drug_id.nunique(),62);self.assertEqual(int(df.eligible.sum()),61)
            self.assertFalse(df[df.drug_id.eq('DB06799')].eligible.any());self.assertEqual(df[df.drug_id.eq('DB00684')].role_relations.sum(),0)
        na=pd.read_csv(QA/'absent_paths_NA.csv');self.assertTrue(na.status.str.startswith('NA_').all())
        paths=pd.read_csv(QA/'protein_path_coverage.csv');self.assertTrue(paths[~paths.train_pool].PPI_path_status.eq('NA_unseen_self_only').all())

    def test_09_coverage_matches_frozen_topology(self):
        before=pd.read_csv(QA/'path_scope_before_attribution.csv');joined=self.coverage.merge(before,on=['context','protocol','drug_id'],validate='one_to_one')
        np.testing.assert_array_equal(joined.role_relations,joined.role_links);np.testing.assert_array_equal(joined.applicable_PPI_pairs,joined.applicable_incident_PPI_pairs)
        for kind,col in [('role','role_relations'),('ppi','applicable_PPI_pairs')]:self.assertEqual(len(self.summary[self.summary.kind.eq(kind)]),int(self.coverage[col].sum())*2)

    def test_10_separate_four_roles_and_single_intervention_keys(self):
        x=self.summary[self.summary.kind.eq('role')];self.assertEqual(set(x.role),set(ROLES))
        self.assertFalse(x.duplicated(['context','drug_id','role','protein_id','mode']).any())
        self.assertTrue(x.groupby(['context','drug_id','role','protein_id']).size().eq(2).all())

    def test_11_no_PT_dictionary_fill(self):
        scope=pd.read_csv(QA/'target_scope.csv');original=pd.read_csv(QA/'original_outputs.csv')
        frozen=json.loads((QA/'frozen_contexts.json').read_text())
        for c in frozen:
            x=original[original.context.eq(c['context'])];self.assertEqual(set(x.class_id),set(c['fitted_targets']));self.assertEqual(len(x),len(c['eligible_ids'])*len(c['fitted_targets']))
            absent=set(scope[scope.context.eq(c['context'])&scope.status.eq('NA_not_fitted')].class_id);self.assertFalse(absent&set(x.class_id))

    def test_12_repeat_permutation_and_query_alone(self):
        df=pd.read_csv(QA/'stability_checks.csv');self.assertEqual(df.context.nunique(),10);self.assertLessEqual(df.max_abs_logit_error.max(),1e-5)
        checks=pd.read_csv(QA/'consistency_checks.csv');self.assertEqual(checks.repeat_error.max(),0)

    def test_13_example_selection_not_outcome_based(self):
        e=pd.read_csv(QA/'examples_frozen.csv');self.assertIn('DB00199',set(e.drug_id))
        for c in json.loads((QA/'frozen_contexts.json').read_text()):
            ids=sorted(c['eligible_ids']);picked=set(ids[:2]+(['DB00199'] if 'DB00199' in ids else []));x=e[e.context.eq(c['context'])]
            self.assertEqual(set(zip(x.drug_id,x.class_id)),{(d,k) for d in picked for k in sorted(c['fitted_targets'])[:2]})

    def test_14_fitting_optimizer_backward_guard(self):
        def forbidden(*a,**k):raise AssertionError('Fit/optimizer/backward forbidden')
        with patch.object(old,'fit_model',forbidden),patch.object(torch.optim.Optimizer,'__init__',forbidden),patch.object(torch.Tensor,'backward',forbidden),torch.no_grad():
            s=self.s;forward(s,cache=cache_for(s['model'],s['g'],0))
        self.assertTrue(all(p.grad is None for p in self.s['model'].parameters()))
        self.assertFalse(any(p.requires_grad for p in self.s['model'].parameters()))

    def test_15_missing_relation_is_rejected_not_zeroed(self):
        s=self.s
        with self.assertRaises(ValueError):resolve_relation(s['g'],s['q'],'absent_drug','target','absent_protein')
        with self.assertRaises(ValueError):pair_index_by_ids(s['g'],'missing1','missing2')

    def test_16_low_zero_effects_and_failures_not_hidden(self):
        self.assertGreater(self.summary.zero_n_abs_tol_1e7.sum(),0)
        self.assertTrue((QA/'attempt_01_technical_failure/failure_evidence.json').exists())
        s=json.loads((QA/'analysis_complete.json').read_text());self.assertFalse(s['WP11_final_closed']);self.assertFalse(s['WP12']);self.assertEqual(s['guarded_fit_optimizer_backward_calls'],0)


if __name__=='__main__':unittest.main(verbosity=2)
