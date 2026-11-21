"""Salt okunur WP11 doğrulamaları: kayıtlı B1, gerçek SHAP, sıfır model fit."""
import inspect,json,sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp11_linear_shap import ROOT,QA,PREP,FEATURES,CHEM,load_context,linear_shap,enumerate_shap,preserve,sha
from wp11_shap_analysis import verify_manifest


class TestWP11SHAP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((QA/'policy_v1.json').read_text());cls.contexts=[load_context(c) for c in cls.policy['contexts']]
        cls.local=pd.read_csv(QA/'local_shap.csv');cls.pairs=pd.read_csv(QA/'local_pair_outputs.csv')
        cls.common=json.loads((QA/'common_PT_intersections.json').read_text());cls.c=cls.contexts[0]

    def test_01_policy_and_frozen_inputs(self):
        self.assertEqual(verify_manifest('policy_commit_before_explanations.json'),6)
        self.assertGreater(verify_manifest('input_manifest.json'),30)

    def test_02_all_prior_artifacts_unchanged(self):self.assertEqual(preserve(),3036)

    def test_03_known_linear_game(self):
        b=np.array([[0,1,2,3,4,1],[2,3,4,5,6,1]],float);x=np.array([[3,4,5,6,7,1]],float);w=np.array([[1,-2,3,-4,5,9]],float)
        out=linear_shap(x,b,w,np.array([2.]));np.testing.assert_allclose(out['phi'][0,0],[2,-4,6,-8,10,0]);self.assertEqual(out['base'][0],26)
        np.testing.assert_allclose(out['base']+out['phi'].sum(2)[0],out['logit'][0])

    def test_04_all_40_real_coalition_checks(self):
        ex=pd.read_csv(QA/'examples_frozen_before_explanations.csv');count=0
        for c in self.contexts:
            out=linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'])
            for r in ex[ex.context.eq(c['context'])].itertuples():
                i=c['test_ids'].index(r.drug_id);j=c['classes'].index(r.class_id);v,base=enumerate_shap(c['test_x'][i],c['train_x'],c['coef'][j],c['intercept'][j])
                np.testing.assert_allclose(v,out['phi'][i,j],rtol=0,atol=1e-10);self.assertAlmostEqual(base,out['base'][j],places=10);count+=1
        self.assertEqual(count,40)

    def test_05_all_saved_OOF_keys_and_scores(self):
        old=pd.read_csv(ROOT/'reports/qa/WP08/baseline_v1/oof_predictions.csv',usecols=['protocol','outer_fold','family','model','drug_id','class_id','score_observed_record_proxy'])
        old=old[old.family.eq('PT')&old.model.eq('B1')];keys=['protocol','outer_fold','drug_id','class_id']
        both=self.pairs.merge(old,on=keys,validate='one_to_one',how='outer',indicator=True,suffixes=('','_saved'))
        self.assertTrue(both['_merge'].eq('both').all());self.assertEqual(len(both),27854)
        np.testing.assert_allclose(both.proxy_score,both.score_observed_record_proxy_saved,rtol=0,atol=1e-12)

    def test_06_additivity_all_real_outputs(self):
        sums=self.local.groupby(['context','drug_id','class_id']).SHAP_logit.sum().rename('independent_sum')
        x=self.pairs.merge(sums,on=['context','drug_id','class_id'],validate='one_to_one')
        np.testing.assert_allclose(x.base+x.independent_sum,x.logit,rtol=0,atol=1e-10)

    def test_07_train_only_exact_background(self):
        for c in self.contexts:
            self.assertEqual(c['train_ids'],c['metadata']['train_drug_ids']);self.assertFalse(set(c['train_ids'])&set(c['inventory_test_ids']))
            self.assertTrue((c['train_x'][:,5]==1).all());self.assertTrue((c['test_x'][:,5]==1).all())

    def test_08_affine_units_equivalence(self):
        raw=pd.read_csv(ROOT/'reports/qa/WP04/chemical_features_clean.csv').set_index('id');stats=json.loads((PREP/'transform_fit_sources_and_statistics.json').read_text())
        for c in self.contexts:
            s=stats[c['context']]['chemistry'];scale=np.array([s['scale'][f] for f in CHEM]);b=raw.loc[c['train_ids'],CHEM].to_numpy();x=raw.loc[c['test_ids'],CHEM].to_numpy()
            expected=(x[:,None,:]-b.mean(0))*(c['coef'][:,:5]/scale)[None,:,:]
            np.testing.assert_allclose(expected,linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'])['phi'][:,:,:5],rtol=0,atol=1e-10)

    def test_09_repeat_and_background_query_target_orders(self):
        for c in self.contexts:
            expected=linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'])
            actual=linear_shap(c['test_x'][::-1],c['train_x'][::-1],c['coef'][::-1],c['intercept'][::-1])
            np.testing.assert_allclose(expected['phi'],actual['phi'][::-1,::-1],rtol=0,atol=1e-12)

    def test_10_heldout_feature_mutation_isolation(self):
        for c in self.contexts:
            x=c['test_x'].copy();before=linear_shap(x,c['train_x'],c['coef'],c['intercept']);x[0,:5]+=1000
            after=linear_shap(x,c['train_x'],c['coef'],c['intercept'])
            np.testing.assert_array_equal(before['base'],after['base']);np.testing.assert_array_equal(before['background_mean'],after['background_mean']);np.testing.assert_array_equal(before['phi'][1:],after['phi'][1:])
            self.assertGreater(np.abs(before['phi'][0]-after['phi'][0]).max(),0)

    def test_11_labels_are_not_explainer_inputs(self):
        self.assertEqual(list(inspect.signature(linear_shap).parameters),['x','background','coef','intercept'])
        c=self.c;a=linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'])
        labels=np.zeros((len(c['test_ids']),len(c['classes'])));labels[:]=1 # No label channel exists.
        b=linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept']);np.testing.assert_array_equal(a['phi'],b['phi'])
        with self.assertRaises(TypeError):linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'],labels=labels)

    def test_12_mask_and_abstentions(self):
        self.assertTrue((self.local[self.local.feature.eq('mask__chemistry')].SHAP_logit==0).all())
        membership=pd.read_csv(QA/'background_test_membership.csv')
        for p in ['primary','stress']:
            m=membership[membership.context.str.startswith(p)&membership.role.eq('TEST_ABSTAIN_QC')];self.assertEqual(m.drug_id.nunique(),8)
            self.assertFalse(set(m.drug_id)&set(self.local[self.local.protocol.eq(p)].drug_id))

    def test_13_no_union_fill_and_common_PT(self):
        for p in ['primary','stress']:
            contexts=[c for c in self.contexts if c['context'].startswith(p)];expected=sorted(set.intersection(*[set(c['classes']) for c in contexts]));self.assertEqual(expected,self.common[p])
        for c in self.contexts:
            frame=self.local[self.local.context.eq(c['context'])];self.assertEqual(set(frame.class_id),set(c['classes']));self.assertEqual(len(frame),len(c['classes'])*len(c['test_ids'])*6)

    def test_14_example_selection_without_outcomes(self):
        examples=pd.read_csv(QA/'examples_frozen_before_explanations.csv')
        for c in self.contexts:
            x=examples[examples.context.eq(c['context'])];expected={(d,k) for d in sorted(c['test_ids'])[:2] for k in sorted(c['classes'])[:2]}
            self.assertEqual(set(zip(x.drug_id,x.class_id)),expected)

    def test_15_background_LOO_exact_sensitivity(self):
        c=self.c;full=linear_shap(c['test_x'],c['train_x'],c['coef'],c['intercept'])
        for j in range(len(c['train_x'])):
            b=np.delete(c['train_x'],j,axis=0);out=linear_shap(c['test_x'],b,c['coef'],c['intercept']);delta=c['coef']*(c['train_x'].mean(0)-b.mean(0))
            np.testing.assert_allclose(out['phi'],full['phi']+delta[None,:,:],rtol=0,atol=1e-12)
            np.testing.assert_array_equal(out['logit'],full['logit']);np.testing.assert_allclose(out['base']+out['phi'].sum(2),out['logit'],rtol=0,atol=1e-10)

    def test_16_global_aggregation_denominators(self):
        saved=pd.read_csv(QA/'global_common_summary.csv')
        for r in saved.itertuples():
            x=self.local[self.local.protocol.eq(r.protocol)&self.local.class_id.isin(self.common[r.protocol])&self.local.feature.eq(r.feature)]
            self.assertEqual(len(x),54*len(self.common[r.protocol]));self.assertAlmostEqual(x.SHAP_logit.abs().mean(),r.mean_abs,places=12)

    def test_17_no_model_fit_or_optimizer_in_new_analysis(self):
        import ast
        for name in ['wp11_linear_shap.py','wp11_shap_analysis.py']:
            tree=ast.parse((ROOT/'scripts'/name).read_text(encoding='utf-8'))
            calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
            self.assertFalse({'fit','fit_transform','backward','step','zero_grad'}&set(calls))

    def test_18_invalid_inputs_rejected(self):
        c=self.c
        with self.assertRaises(ValueError):linear_shap(c['test_x'][:,:5],c['train_x'],c['coef'],c['intercept'])
        with self.assertRaises(ValueError):linear_shap(c['test_x'],c['train_x'][:0],c['coef'],c['intercept'])
        x=c['test_x'].copy();x[0,0]=np.nan
        with self.assertRaises(ValueError):linear_shap(x,c['train_x'],c['coef'],c['intercept'])


if __name__=='__main__':unittest.main(verbosity=2)
