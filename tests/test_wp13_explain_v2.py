import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_explain_v2 as m
class Explain(unittest.TestCase):
 def test_01_positive_SHAP(self):
  s=m.shap_sentence({'SHAP_logit':0.5,'feature':'chem__MW','feature_type':'chemistry'});self.assertIn('artırıcı',s);self.assertIn('0.5',s)
 def test_02_negative_SHAP(self):self.assertIn('azaltıcı',m.shap_sentence({'SHAP_logit':-0.3,'feature':'chem__LogP','feature_type':'chemistry'}))
 def test_03_mask_not_chemistry(self):self.assertIn('Eksiklik/modalite maskesi',m.shap_sentence({'SHAP_logit':0,'feature':'mask__chemistry','feature_type':'mask'}))
 def test_04_delta_positive_removal_decreases(self):self.assertIn('logit azaldı',m.delta_sentence({'mode':'fixed','delta_z':.2,'status':'OK'}))
 def test_05_delta_negative_removal_increases(self):self.assertIn('logit arttı',m.delta_sentence({'mode':'fixed','delta_z':-.2,'status':'OK'}))
 def test_06_methods_distinct(self):self.assertIn('yeniden normalizasyon',m.delta_sentence({'mode':'delete','delta_z':.2,'status':'OK'}))
 def test_07_NA_not_zero(self):self.assertIn('NA',m.delta_sentence({'mode':'fixed','delta_z':None,'status':'NA'}))
 def test_08_wrong_fold(self):
  with self.assertRaisesRegex(ValueError,'MISMATCH'):m.get('DB00199','C0000731',1)
 def test_09_wrong_PT(self):
  with self.assertRaisesRegex(ValueError,'MISMATCH'):m.get('DB00199','NEW',3)
 def test_10_wrong_model(self):
  row=m.get('DB00199','C0000731',3)['graph'][:1]
  with self.assertRaisesRegex(ValueError,'MODEL_MISMATCH'):m.guard(row,'DB00199','C0000731',3,'B1')
 def test_11_wrong_drug(self):
  row=m.get('DB00199','C0000731',3)['graph'][:1]
  with self.assertRaisesRegex(ValueError,'MISMATCH'):m.guard(row,'DB00254','C0000731',3,'A1P1')
 def test_12_real_math_two_PT_both_drugs(self):
  pairs=m.old.pd.read_csv(m.ROOT/'reports/qa/WP11/B1_SHAP_v1/local_pair_outputs.csv')
  for p,f in [('DB00199',3),('DB00254',1)]:
   for pt in ['C0000731','C0000737']:
    a=m.get(p,pt,f);self.assertEqual(len(a['shap']),6)
    r=pairs[(pairs.protocol=='primary')&pairs.drug_id.eq(p)&pairs.class_id.eq(pt)].iloc[0]
    self.assertAlmostEqual(r['base']+sum(s['SHAP_logit'] for s in a['shap']),r['logit'],places=8)
    self.assertAlmostEqual(1/(1+math.exp(-r['logit'])),r.proxy_score,places=8)
    for g in a['graph']:self.assertAlmostEqual(g['original_logit']-g['intervened_logit'],g['delta_z'],places=6)
 def test_13_no_specific_explanation_from_general_inputs(self):
  self.assertIn('NOT_AVAILABLE',(m.ROOT/'apps/drug_safety_explorer_FINAL_v2.py').read_text(encoding='utf-8'))
 def test_14_complete_existing_coverage(self):
  self.assertEqual(len(m.available('DB00199')['graph']),318);self.assertEqual(len(m.available('DB00254')['shap']),220)
 def test_15_raw_magnitude_preserved(self):
  v=-0.000000123456789;self.assertIn(repr(v),m.shap_sentence({'SHAP_logit':v,'feature':'chem__MW','feature_type':'chemistry'}))
if __name__=='__main__':unittest.main(verbosity=2)
