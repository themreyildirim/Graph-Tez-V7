import unittest,sys,math
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_final_data_v1 as m
class FinalDemo(unittest.TestCase):
 def test_01_ownfold_keys(self):
  for p,f,n in [('DB00199',3,318),('DB00254',1,240)]:
   d=m.recorded(p);self.assertEqual(d['fold'],f);self.assertEqual(len(d['predictions']),n);self.assertEqual(len({r['class_id'] for r in d['predictions']}),n)
 def test_02_prediction_without_PDF(self):
  with patch.object(m.tr,'load',side_effect=AssertionError('PDF must not be read')):self.assertTrue(m.recorded('DB00199')['predictions'])
 def test_03_unknown_drug(self):
  with self.assertRaisesRegex(ValueError,'NOT_SUPPORTED'):m.recorded('NEW')
 def test_04_source_single_term(self):
  c=m.tr.load(0)['candidates'][0];v=m.source_view(c);self.assertEqual(v['term'],'Nefes darlığı');self.assertIn('Baygınlık',v['full_section']);self.assertNotIn('Baygınlık',v['term']);self.assertEqual(m.tr.load(0)['pages'][5]['text'][v['start']:v['end']],v['term'])
 def test_05_known_upload_hash(self):
  for i,f in enumerate(m.tr.FILES):self.assertEqual(m.upload((m.ROOT/'data/user_pdfs'/f).read_bytes(),f)['index'],i)
 def test_06_unknown_readable_PDF(self):
  from wp12_pilot import get_engine
  with get_engine().open() as doc:
   doc.new_page().insert_text((50,50),'Package leaflet. Possible side effects: experimental text.')
   r=m.upload(doc.tobytes(),'unknown.pdf')
  self.assertIsNone(r['index']);self.assertEqual(r['GNN'],'NOT_SUPPORTED');self.assertEqual(r['status'],'UNVERIFIED');self.assertTrue(r['windows'])
 def test_07_blank_PDF(self):
  from wp12_pilot import get_engine
  with get_engine().open() as doc:doc.new_page();r=m.upload(doc.tobytes(),'blank.pdf')
  self.assertFalse(r['windows']);self.assertEqual(r['OCR'],'OCR_NOT_AVAILABLE')
 def test_08_size_invalid_limits(self):
  for content in [b'bad',b'%PDF-'+b'0'*(20*1024*1024)]:
   with self.assertRaises(ValueError):m.upload(content,'bad.pdf')
 def test_09_no_invented_mapping(self):
  for i in range(2):self.assertTrue(all(r['PT eşlemesi']=='UNMAPPED' and r['İnsan kararı']=='PENDING' for r in m.comparison(m.tr.load(i))))
 def test_10_attribution_exact_target(self):
  for p in m.PARENTS:
   b=m.recorded(p);a=m.attribution(b,'C0000731');self.assertTrue(a['graph']);self.assertTrue(a['SHAP_B1']);self.assertTrue(all(r['drug_id']==p and r['class_id']=='C0000731' and r['outer_fold']==b['fold'] for r in a['graph']+a['SHAP_B1']))
 def test_11_absent_target_not_other_explanation(self):
  a=m.attribution(m.recorded('DB00199'),'NOT_A_PT');self.assertFalse(a['graph'] or a['SHAP_B1'])
 def test_12_intervention_math_and_NA(self):
  for p in m.PARENTS:
   for r in m.recorded(p)['graph']:
    if r['status']=='OK':self.assertAlmostEqual(r['original_logit']-r['intervened_logit'],r['delta_z'],places=6)
    else:self.assertIsNone(r['delta_z'])
 def test_13_shap_additive_separate_model(self):
  for p in m.PARENTS:
   b=m.recorded(p)
   for r in b['shap_outputs']:
    rows=[s for s in b['shap'] if s['class_id']==r['class_id']]
    if rows:self.assertAlmostEqual(sum(s['SHAP_logit'] for s in rows)+r['base'],r['logit'],places=8)
 def test_14_UI_no_network_training(self):
  t=(m.ROOT/'apps/drug_safety_explorer_FINAL_v1.py').read_text(encoding='utf-8');self.assertIn('st.file_uploader',t);self.assertIn('Prospektüsteki tam bölüm',t);self.assertNotIn('import openai',t);self.assertNotIn('.fit(',t);self.assertNotIn('requests.',t)
 def test_15_page_limit(self):
  from wp12_pilot import get_engine
  with get_engine().open() as d:
   for _ in range(121):d.new_page()
   with self.assertRaisesRegex(ValueError,'PAGE_LIMIT'):m.upload(d.tobytes(),'too_many.pdf')
 def test_16_character_limit(self):
  from unittest.mock import MagicMock
  page=MagicMock();page.get_text.return_value='x'*2000001
  pdf=MagicMock();pdf.needs_pass=False;pdf.__len__.return_value=1;pdf.__iter__.return_value=iter([page])
  engine=MagicMock();engine.open.return_value.__enter__.return_value=pdf
  with patch.object(m.tr.core,'get_engine',return_value=engine):
   with self.assertRaisesRegex(ValueError,'TEXT_LIMIT'):m.upload(b'%PDF-test','large_text.pdf')
if __name__=='__main__':unittest.main(verbosity=2)
