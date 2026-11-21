import unittest,sys,itertools,math,json
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_tedizolid_SHAP_v1 as m
class SHAP(unittest.TestCase):
 def test_01_original_lock_exact(self):self.assertEqual(m.public_sha(m.PRED/'prediction_lock.json'),m.EXPECTED);m.verify_predictions()
 def test_02_pre_selection_is_locked_top10(self):
  p=m.verify_pre();r=pd.read_csv(m.PRED/'common201_scores.csv',float_precision='round_trip');self.assertEqual([x['class_id'] for x in p['method']['selected']],r.head(10).class_id.tolist())
 def test_03_five_backgrounds_train_only(self):
  for b in m.verify_pre()['backgrounds']:
   meta=m.read(m.ROOT/b['model_json']);self.assertEqual(b['train_ids'],meta['train_drug_ids']);self.assertFalse(set(b['train_ids'])&set(meta['test_drug_ids_never_fit']));self.assertNotIn('DB14569',b['train_ids'])
 def test_04_positive_negative_zero(self):
  self.assertIn('artırıcı',m.sentence('MW',.2));self.assertIn('azaltıcı',m.sentence('MW',-.2));self.assertIn('sıfır katkı',m.sentence('MW',0))
 def test_05_mask_is_separate(self):self.assertIn('kimyasal tanımlayıcı değil',m.sentence('mask',0,True))
 def test_06_preserve_raw_numeric_sign(self):self.assertIn(repr(-.0000123456789),m.sentence('MW',-.0000123456789))
 def test_07_synthetic_exact_interventional_game(self):
  x=np.array([2.,-.7,1.2,0.,3.,1.]);b=np.array([[0.,1.,2.,3.,4.,1.],[1.,2.,1.,0.,-2.,1.]])
  w=np.array([[.1,-.4,.7,.3,-.1,.8]]);a=np.array([-.5]);phi,base,mu=m.exact_phi_base(x,b,w,a)
  values={}
  for bits in itertools.product([False,True],repeat=6):
   mixed=b.copy();mixed[:,bits]=x[np.array(bits)];values[bits]=float(np.mean(mixed@w[0]+a[0]))
  independent=np.zeros(6)
  for j in range(6):
   for bits,v in values.items():
    if bits[j]:continue
    k=sum(bits);other=list(bits);other[j]=True
    independent[j]+=math.factorial(k)*math.factorial(5-k)/math.factorial(6)*(values[tuple(other)]-v)
  self.assertTrue(np.allclose(phi[0],independent,atol=1e-12));self.assertAlmostEqual(base[0],values[(False,)*6],places=12)
 def test_08_no_sigmoid_additive_interpretation(self):
  self.assertEqual(m.verify_pre()['method']['scale'],'per-model B1 LOGIT only');self.assertTrue(m.verify_pre()['method']['no_ensemble_SHAP'])
 def test_09_invalid_shape_or_nonfinite(self):
  for x in [np.zeros(5),np.array([np.nan]*6)]:
   with self.assertRaises(ValueError):m.exact_phi_base(x,np.zeros((2,6)),np.zeros((1,6)),np.zeros(1))
 def test_10_uniform_background_formula(self):
  x=np.arange(6.);b=np.vstack([np.zeros(6),np.ones(6)*2]);phi,base,mu=m.exact_phi_base(x,b,np.ones((1,6)),np.zeros(1));self.assertTrue(np.array_equal(mu,np.ones(6)))
if __name__=='__main__':unittest.main(verbosity=2)
