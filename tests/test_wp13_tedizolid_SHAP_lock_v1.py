import unittest,sys
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_tedizolid_SHAP_v1 as m
class ActualLock(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lock=m.read(m.Q/'explanation_lock.json');cls.f=pd.read_csv(m.Q/'local_feature_SHAP.csv',float_precision='round_trip');cls.p=pd.read_csv(m.Q/'pair_additivity.csv',float_precision='round_trip');cls.c=pd.read_csv(m.Q/'coverage.csv')
 def test_01_explanation_lock_hash(self):self.assertEqual(m.public_sha(m.Q/'explanation_lock.json'),m.read(m.Q/'explanation_lock_sha256.json')['sha256'])
 def test_02_sources_and_outputs(self):m.checks(self.lock['source_pins']);m.checks(self.lock['outputs_sha256']);m.verify_predictions()
 def test_03_count_and_unique_keys(self):self.assertEqual(len(self.f),300);self.assertFalse(self.f.duplicated(['fold','class_id','feature']).any());self.assertEqual(len(self.p),50)
 def test_04_first10_five_models_only(self):
  chosen={r['class_id'] for r in m.read(m.Q/'method_policy.json')['selected']};self.assertEqual(set(self.f.class_id),chosen);self.assertEqual(set(self.f.fold),{1,2,3,4,5})
 def test_05_additivity_against_locked_logits(self):
  summed=self.f.groupby(['fold','class_id']).SHAP_logit.sum()
  for r in self.p.itertuples():self.assertLess(abs(r.base_logit+summed.loc[(r.fold,r.class_id)]-r.locked_logit),1e-10)
 def test_06_locked_score_not_repredicted(self):
  for fold in range(1,6):
   locked=pd.read_csv(m.PRED/f'fold{fold}_scores.csv',float_precision='round_trip').set_index('class_id')
   for r in self.p[self.p.fold.eq(fold)].itertuples():self.assertEqual(r.locked_logit,locked.loc[r.class_id,'logit']);self.assertEqual(r.locked_record_score,locked.loc[r.class_id,'record_ranking_score']);self.assertLess(abs(expit(r.base_logit+r.sum_phi)-r.locked_record_score),1e-12)
 def test_07_each_feature_formula(self):self.assertTrue(np.allclose(self.f.coefficient*(self.f.standardized_query-self.f.background_mean_standardized),self.f.SHAP_logit,atol=1e-14,rtol=0))
 def test_08_mask_separate_and_zero_local_contrast(self):
  mask=self.f[self.f.feature.eq('mask__chemistry')];self.assertEqual(len(mask),50);self.assertTrue(mask.feature_type.eq('availability_mask').all());self.assertTrue(mask.SHAP_logit.eq(0).all());self.assertTrue(mask.raw_value.eq(1).all())
 def test_09_train_background_mean_and_ids(self):
  for b in m.verify_pre()['backgrounds']:
   with np.load(m.ROOT/b['feature_file'],allow_pickle=False) as f:
    ids=list(f['drug_ids'].astype(str));mean=f['B1'][[ids.index(d) for d in b['train_ids']]].mean(0)
   summary=m.read(m.Q/'background_summary.json');rows=[r for r in summary if r['fold']==b['fold']];self.assertTrue(np.array_equal(mean,np.array([r['mean_standardized'] for r in rows])))
 def test_10_NOT_RUN_outside_selection(self):self.assertEqual(sum(self.c.status.eq('EXPLAINED')),50);self.assertEqual(sum(self.c.status.eq('NOT_RUN')),1244);self.assertEqual(self.lock['outside_common201_top10_PT'],191)
 def test_11_verbal_signs_and_values(self):
  for r in self.f.itertuples():
   expected='artırıcı' if r.SHAP_logit>0 else 'azaltıcı' if r.SHAP_logit<0 else 'sıfır katkı';self.assertIn(expected,r.comment_tr);self.assertIn(repr(float(r.SHAP_logit)),r.comment_tr)
 def test_12_no_ensemble_or_predict(self):self.assertTrue(self.lock['no_ensemble_SHAP']);self.assertEqual(self.lock['new_model_predict_calls'],0);self.assertFalse(self.lock['reference_access'])
 def test_13_started_after_selection(self):self.assertLessEqual(m.read(m.Q/'pre_explanation_manifest.json')['created_utc'],m.read(m.Q/'explanation_started.json')['created_utc'])
 def test_14_no_retry(self):
  before=m.public_sha(m.Q/'explanation_lock.json')
  with self.assertRaisesRegex(RuntimeError,'NO_AUTORETRY'):m.explain()
  self.assertEqual(before,m.public_sha(m.Q/'explanation_lock.json'))
if __name__=='__main__':unittest.main(verbosity=2)
