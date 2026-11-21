import unittest,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_tr_sources_v1 as m
class TurkishSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.docs=[m.load(i) for i in range(2)]
 def test_01_raw_identity_and_all_pages(self):
  for i,d in enumerate(self.docs):
   self.assertEqual(d['sha256'],m.EXPECTED[i]);fresh=m.core.extract_pdf((m.ROOT/'data/user_pdfs'/m.FILES[i]).read_bytes());self.assertEqual(d['pages'],fresh['pages']);self.assertEqual(d['page_count'],[8,13][i])
 def test_02_real_text_spans(self):
  for d in self.docs:self.assertTrue(m.validate(d))
 def test_03_correct_compound_salt_dose(self):
  a,b=self.docs;self.assertIn('750 mg eritromisin stearat',m.norm(a['record']['identity_evidence']['quote_exact']));self.assertIn('115,414 mg doksisiklin hiklat',m.norm(b['record']['identity_evidence']['quote_exact']));self.assertEqual([d['record']['salt'] for d in self.docs],['eritromisin stearat','doksisiklin hiklat'])
 def test_04_KT_KUB_and_no_assumed_version(self):
  self.assertEqual([d['record']['document_type'] for d in self.docs],['KT','KÜB'])
  for d in self.docs:self.assertEqual(d['record']['currentness'],'UNVERIFIED_CURRENTNESS');self.assertEqual(d['record']['document_revision_date'],'NOT_AVAILABLE_EMPTY_FIELD')
  self.assertEqual(self.docs[1]['record']['filename_date_hint'],'07-11-2018_UNVERIFIED')
 def test_05_not_English_product_equivalence(self):
  for d in self.docs:self.assertEqual(d['record']['English_product_equivalence'],'NOT_ESTABLISHED')
 def test_06_ER_counts_from_bullets_not34(self):
  s=m.statistics(self.docs[0]);self.assertEqual(s['records'],25);self.assertEqual(s['frequency'],{'RARE_SOURCE_WORDING':6,'UNKNOWN':19})
 def test_07_MO_actual_terms_and_repeated_glossit(self):
  s=m.statistics(self.docs[1]);self.assertEqual((s['records'],s['unique_source_terms']),(48,47));self.assertEqual(s['repeats'],{'glossit':2})
 def test_08_scope_frequency_not_clinical_confirmation(self):
  for d in self.docs:
   for c in d['candidates']:self.assertEqual(c['status'],'PENDING');self.assertEqual(c['MedDRA'],'UNMAPPED');self.assertEqual(c['statement_kind'],'adverse_candidate')
 def test_09_serious_ER_frequency_other_page(self):
  a=self.docs[0]['candidates'][0];self.assertEqual(a['source']['physical_page'],6);self.assertEqual(a['frequency_quote']['physical_page'],7);self.assertIn('oldukça seyrek',a['frequency_exact'])
 def test_10_unknown_never_imputed_rare(self):
  for d in self.docs:
   for c in d['candidates']:
    if c['frequency_state']=='UNKNOWN':self.assertIn('Bilinmiyor',c['frequency_exact'])
 def test_11_overdose_not_candidate_source(self):
  for d in self.docs:
   self.assertTrue(any(c['statement_kind']=='overdose' for c in d['contexts']))
   for c in d['candidates']:self.assertNotIn('aşırı dozu',c['source']['quote_exact']);self.assertNotIn('4.9',c['source']['quote_exact'])
 def test_12_animal_never_human_adverse(self):
  d=self.docs[1];self.assertTrue(any(q['statement_kind']=='animal_study' for q in d['contexts']));self.assertFalse(any('hayvanlarda' in c['source']['quote_exact'].lower() for c in d['candidates']))
 def test_13_BUN_not_accumulation_absence(self):
  c=next(c for c in self.docs[1]['candidates'] if c['name_tr']=='BUN artışı');self.assertEqual(c['frequency_state'],'UNKNOWN');self.assertEqual(c['source']['physical_page'],10);self.assertEqual([q['scope'] for q in c['context_quotes']],['class_level','product_specific']);self.assertIn('akümülasyona neden olmadığını',m.norm(c['context_quotes'][1]['quote_exact']));self.assertIn('BUN artışının yokluğu değildir',c['source_note'])
 def test_14_class_scope_not_all_MO(self):
  rows=self.docs[1]['candidates'];self.assertEqual(next(c for c in rows if c['name_tr']=='Özofajit')['scope'],'class_level');self.assertEqual(next(c for c in rows if c['name_tr']=='BUN artışı')['scope'],'product_specific');self.assertEqual(next(c for c in rows if c['name_tr']=='disfaji')['scope'],'unresolved')
 def test_15_thyroid_negative_function_retained(self):
  c=next(c for c in self.docs[1]['candidates'] if 'kahverengi-siyah' in c['name_tr']);self.assertIn('anormallik olduğu bilinmemektedir',m.norm(c['source']['quote_exact']))
 def test_16_no_old_LLM_on_new_source(self):
  for d in self.docs:
   for c in d['candidates']:self.assertEqual(m.saved_explanations(c),[]);self.assertTrue(c['source']['quote_id'].startswith('trquote:'))
 def test_17_wrong_raw_hash_rejected(self):
  from unittest.mock import patch
  with patch.object(m,'EXPECTED',['WRONG',m.EXPECTED[1]]):
   with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):m.build(0)
 def test_18_invalid_anchor_rejected(self):
  with self.assertRaisesRegex(ValueError,'ANCHOR_NOT_FOUND'):m.locate('okunabilir metin','uydurma ifade')
 def test_19_new_UI_no_network_or_fit(self):
  text=(m.ROOT/'apps/drug_safety_explorer_TR_v1.py').read_text(encoding='utf-8');self.assertNotIn('import openai',text);self.assertNotIn('requests.',text);self.assertNotIn('.fit(',text);self.assertIn('Türkçe belge',text)
 def test_20_selection_namespace_and_row_alignment(self):
  import wp13_presentation_v1_2 as s
  a=[c['candidate_id'] for c in self.docs[0]['candidates']];b=[c['candidate_id'] for c in self.docs[1]['candidates']];state={};s.init_selection(state,'er',a);s.init_selection(state,'mo',b);state['t']={'selection':{'rows':[5]}};s.table_changed(state,'mo',b,'t');self.assertEqual(state['mo_picker'],b[5]);self.assertEqual(state['er_active'],a[0]);self.assertEqual(state['mo_active'],b[5])
 def test_21_duplicate_display_names_have_distinct_labels(self):
  for d in self.docs:
   labels=[m.candidate_label(c) for c in d['candidates']];self.assertEqual(len(labels),len(set(labels)))
  gloss=[c for c in self.docs[1]['candidates'] if c['name_tr']=='glossit'];self.assertEqual(len(gloss),2);self.assertNotEqual(m.candidate_label(gloss[0]),m.candidate_label(gloss[1]));self.assertIn('sayfa 9',m.candidate_label(gloss[0]));self.assertIn('sayfa 10',m.candidate_label(gloss[1]))
if __name__=='__main__':unittest.main(verbosity=2)
