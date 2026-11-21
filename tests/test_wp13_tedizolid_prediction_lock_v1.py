"""Post-lock validation only. Never invokes real model inference."""
import unittest,sys
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_tedizolid_B1_external_v1 as m
class LockedPrediction(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lock=m.read(m.Q/'prediction_lock.json');cls.policy=m.read(m.Q/'approved_policy.json')
  cls.frames=[pd.read_csv(m.Q/f'fold{i}_scores.csv',float_precision='round_trip') for i in range(1,6)]
  cls.common=pd.read_csv(m.Q/'common201_scores.csv',float_precision='round_trip')
 def test_01_lock_digest(self):self.assertEqual(m.public_sha(m.Q/'prediction_lock.json'),m.read(m.Q/'prediction_lock_sha256.json')['prediction_lock_sha256'])
 def test_02_all_outputs_hash(self):m.check_hashes(self.lock['outputs_sha256'])
 def test_03_inputs_and_models_immutable(self):m.check_hashes(self.lock['input_and_models_sha256']);m.verify_precommit()
 def test_04_one_query_five_models(self):self.assertEqual(self.lock['query_count'],1);self.assertEqual(self.lock['forward_calls'],5);self.assertEqual(self.lock['individual_targets'],[220,262,267,270,275])
 def test_05_order_precommit_before_inference_before_lock(self):
  a=m.read(m.Q/'precommit_manifest.json')['created_utc'];b=m.read(m.Q/'inference_started.json')['created_utc'];self.assertLessEqual(a,b);self.assertLessEqual(b,self.lock['created_utc'])
 def test_06_exact_head_membership(self):
  for model,f in zip(m.read(m.Q/'precommit_manifest.json')['models'],self.frames):self.assertEqual(set(model['classes']),set(f.class_id));self.assertEqual(f.class_id.nunique(),len(f));self.assertEqual(set(f.fold),{model['fold']})
 def test_07_finite_score_and_logit_semantics(self):
  for f in self.frames:self.assertTrue(np.isfinite(f.logit).all());self.assertTrue(f.record_ranking_score.between(0,1).all());self.assertTrue(np.allclose(expit(f.logit),f.record_ranking_score,atol=1e-15,rtol=0))
 def test_08_CSV_JSON_equal(self):
  for i,f in enumerate(self.frames,1):
   raw=m.read(m.Q/f'fold{i}_scores.json');self.assertEqual(f.class_id.tolist(),[r['class_id'] for r in raw]);self.assertTrue(np.array_equal(f.record_ranking_score.to_numpy(),np.array([r['record_ranking_score'] for r in raw])))
 def test_09_rank_policy(self):
  for f in self.frames+[self.common]:self.assertEqual(f['rank'].tolist(),list(range(1,len(f)+1)));self.assertEqual(f.class_id.tolist(),f.sort_values(['record_ranking_score','class_id'],ascending=[False,True]).class_id.tolist())
 def test_10_equal_mean_201_no_fill(self):
  expected,matrix=m.common_summary(self.frames,self.policy['common_classes']);self.assertEqual(len(self.common),201);self.assertEqual(self.common.class_id.tolist(),expected.class_id.tolist());self.assertTrue(np.array_equal(expected.record_ranking_score.to_numpy(),self.common.record_ranking_score.to_numpy()))
 def test_11_common_contributing_scores_equal_individuals(self):
  for i,f in enumerate(self.frames,1):self.assertTrue(np.array_equal(self.common[f'fold{i}_score'].to_numpy(),f.set_index('class_id').loc[self.common.class_id,'record_ranking_score'].to_numpy()))
 def test_12_excluded_experiments_NOT_RUN(self):
  for field in ['DB09042','stress','A1P1']:self.assertEqual(self.lock[field],'NOT_RUN')
  self.assertEqual(self.lock['SHAP'],'DEFERRED_NOT_RUN');self.assertFalse(self.lock['reference_access'] or self.lock['source_labels_accessed'])
 def test_13_repeat_blocked_before_model_access(self):
  h=m.public_sha(m.Q/'prediction_lock.json')
  with self.assertRaisesRegex(RuntimeError,'NO_RETRY'):m.infer()
  self.assertEqual(h,m.public_sha(m.Q/'prediction_lock.json'))
if __name__=='__main__':unittest.main(verbosity=2)
