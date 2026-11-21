import sys,unittest,json
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_candidates_v1_1 as m
class Candidates(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=m.core.verified_document('pil.502.pdf');cls.d=m.core.verified_document('050641Orig1s032lbl.pdf')
  cls.er=m.known(cls.e);cls.dr=m.known(cls.d)
 def test_01_two_real_source_tables_nonempty(self):
  self.assertGreater(len(self.er),20);self.assertGreater(len(self.dr),20)
 def test_02_candidate_spans_and_quote_identity(self):
  for doc,rows in [(self.e,self.er),(self.d,self.dr)]:
   source={q['quote_id']:q for q in doc['quotes']}
   for c in rows:
    q=source[c['quote_id']];page=doc['pages'][c['physical_page']-1]['text']
    self.assertEqual(page[c['term_start']:c['term_end']],c['source_term']);self.assertEqual(page[c['quote_start']:c['quote_end']],c['quote_exact']);self.assertEqual(q['document_id'],c['document_id'])
 def test_03_no_clinical_or_PT_approval(self):
  self.assertTrue(all(c['status']=='CANDIDATE_PENDING_HUMAN' and c['MedDRA_mapping']=='UNMAPPED' for c in self.er+self.dr))
 def test_04_unknown_frequency_local_not_global(self):
  self.assertTrue(all(c['frequency']=='UNKNOWN' for c in self.er if c['source_key']=='E_unknown_frequency'))
  self.assertEqual(next(c for c in self.er if c['source_term']=='diarrhoea')['frequency'],'NOT_SPECIFIED')
 def test_05_D_direct_vs_class_diarrhea(self):
  rows=[c for c in self.dr if c['source_term'].lower()=='diarrhea'];self.assertEqual(len(rows),2)
  self.assertEqual({(c['scope'],c['frequency']) for c in rows},{('drug_direct','infrequent'),('class_level','NOT_SPECIFIED')})
 def test_06_rare_uncommon_exact_source_words(self):
  for c in self.dr:
   if c['frequency']!='NOT_SPECIFIED':self.assertIn(c['frequency_source'],c['quote_exact'])
 def test_07_BUN_exception_in_two_original_sentences(self):
  c=next(c for c in self.dr if c['source_key']=='D_class_renal');self.assertEqual(c['scope'],'class_level')
  text=' '.join(q['quote'] for q in c['context_quotes']);self.assertIn('does not occur',text);self.assertIn('impaired renal function',text)
 def test_08_overlap_not_independent_evidence(self):
  for rows in [self.er,self.dr]:
   self.assertEqual(len({(c['document_id'],c['term_start'],c['term_end'],c['physical_page']) for c in rows}),len(rows));self.assertTrue(all(not c['is_independent_clinical_evidence'] for c in rows))
 def test_09_multiple_source_effects_separate(self):
  names={c['name_tr'] for c in self.dr};self.assertTrue({'Bulantı','Kusma','Glossit','Yutma güçlüğü'}.issubset(names))
 def test_10_no_wrong_S01_identity_explanation(self):
  for c in self.er:
   self.assertTrue(all(r['scenario']!='S01' for r in m.explanation(c,'pil.502.pdf')))
 def test_11_selected_hearing_real_S04_replay(self):
  c=next(c for c in self.er if c['name_tr']=='Geri dönüşlü işitme kaybı');rows=m.explanation(c,'pil.502.pdf')
  self.assertGreater(len(rows),0);self.assertTrue(all('işitme kaybı' in r['model_explanation_exact'] for r in rows))
 def test_12_uncovered_effect_no_explanation(self):
  c=next(c for c in self.dr if c['name_tr']=='Glossit');self.assertEqual(m.explanation(c,'050641Orig1s032lbl.pdf'),[])
 def test_13_unknown_identity_gnn_unavailable(self):self.assertEqual(m.gnn_named({'mode':'EXPERIMENTAL_UPLOAD'})['status'],'NOT_AVAILABLE')
 def test_14_gnn_names_real_scope(self):
  for d,n in [(self.e,318),(self.d,240)]:
   g=m.gnn_named(d);self.assertEqual(g['targets'],n);self.assertTrue(all(r['target_name'] and r['class_id'].startswith('C') for r in g['rows']))
 def test_15_real_upload_experimental_not_verified(self):
  d=m.core.extract_pdf((m.core.ROOT/'data/user_pdfs/050641Orig1s032lbl.pdf').read_bytes());rows=m.experimental(d)
  self.assertGreater(len(rows),0);self.assertTrue(all(c['scope']=='UNVERIFIED' and c['status']=='EXPERIMENTAL_PENDING_HUMAN' for c in rows))
 def test_16_empty_and_image_only_no_candidates(self):
  for status in ['NO_TEXT','IMAGE_TEXT_UNAVAILABLE']:
   self.assertEqual(m.experimental({'pages':[{'text':'','physical_page':1,'status':status}],'document_id':'TEST_ONLY'}),[])
 def test_17_unsupported_source_text_not_forced(self):
  doc={'pages':[{'text':'ADVERSE REACTIONS\nUnparseable condition XYZ','physical_page':1,'status':'TEXT_AVAILABLE'}],'document_id':'TEST_ONLY'}
  self.assertEqual(m.experimental(doc),[])
 def test_18_wrong_pdf_identity(self):
  with self.assertRaises(ValueError):m.core.match_upload((m.core.ROOT/'data/user_pdfs/pil.502.pdf').read_bytes(),'DB00254')
 def test_19_no_new_API_code_in_ui(self):
  s=(m.core.ROOT/'apps/drug_safety_explorer_v1_1.py').read_text(encoding='utf-8');self.assertNotIn('run_from_ui',s);self.assertNotIn('OPENAI_API_KEY',s)
 def test_20_light_theme(self):
  import tomllib
  t=tomllib.loads((m.core.ROOT/'.streamlit/config.toml').read_text(encoding='utf-8'));self.assertEqual(t['theme']['base'],'light')
if __name__=='__main__':unittest.main(verbosity=2)
