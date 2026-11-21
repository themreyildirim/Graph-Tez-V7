import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_presentation_v1_2 as m
class Presentation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=m.known(m.core.verified_document('pil.502.pdf'));cls.d=m.known(m.core.verified_document('050641Orig1s032lbl.pdf'))
 def test_01_exact_counts(self):
  a=m.counts(self.e);b=m.counts(self.d)
  self.assertEqual((a['records'],a['unique_source_terms'],a['unique_Turkish_names']),(34,34,34))
  self.assertEqual((b['records'],b['unique_source_terms'],b['unique_Turkish_names']),(34,33,33))
 def test_02_scopes_and_repeat_not_independent(self):
  a=m.counts(self.e);b=m.counts(self.d);self.assertEqual(a['scope_counts'],{'product_specific':34});self.assertEqual(b['scope_counts'],{'drug_direct':1,'class_level':33});self.assertEqual(b['repeated_terms'][0]['normalized_source_term'],'diarrhea');self.assertEqual(b['clinical_validated_count'],'NOT_ESTABLISHED')
 def test_03_v11_candidate_bytes_equivalent(self):
  old=m.core.read(m.original.QA/'candidate_records.json');self.assertEqual(old,self.e+self.d)
 def test_04_editorial_not_LLM_and_pending(self):
  for c in self.e+self.d:
   s=m.editorial(c);self.assertEqual(s['candidate_id'],c['candidate_id']);self.assertFalse(s['LLM_generated']);self.assertEqual(s['review'],'PENDING');self.assertEqual(s['source_quote_id'],c['quote_id'])
 def test_05_unknown_not_translated_rare_or_common(self):
  for c in self.e:
   if c['frequency']=='UNKNOWN':
    text=m.editorial(c)['frequency_tr'];self.assertIn('bilinmiyor',text);self.assertNotIn('nadir',text);self.assertNotIn('yaygın',text)
 def test_06_BUN_condition_scope(self):
  c=next(c for c in self.d if c['source_key']=='D_class_renal');s=m.editorial(c)
  self.assertIn('sınıfına',s['scope_tr']);self.assertIn('böbrek işlevi bozulmuş',s['condition_tr']);self.assertIn('Bugüne kadarki çalışmalar',s['condition_tr']);self.assertIn('ortaya çıkmadığını',s['condition_tr'])
 def test_07_usually_preserved(self):
  c=next(c for c in self.e if c['name_tr']=='Geri dönüşlü işitme kaybı');self.assertIn('genellikle',m.editorial(c)['condition_tr'])
 def test_08_unknown_scope_untranslated_retained(self):
  c={**self.e[0],'scope':'UNVERIFIED','source_key':'EXPERIMENTAL'};s=m.editorial(c);self.assertIn('NOT_AVAILABLE',s['scope_tr']);self.assertIn('NOT_AVAILABLE',s['frequency_tr'])
 def test_09_picker_updates_active_and_table_epoch(self):
  ids=[c['candidate_id'] for c in self.e];state={};m.init_selection(state,'x',ids);state['x_picker']=ids[4];m.picker_changed(state,'x',ids)
  self.assertEqual(state['x_active'],ids[4]);self.assertEqual(state['x_epoch'],1)
 def test_10_row_updates_picker_active_same_ID(self):
  ids=[c['candidate_id'] for c in self.d];state={};m.init_selection(state,'x',ids);state['table']={'selection':{'rows':[6]}};m.table_changed(state,'x',ids,'table')
  self.assertEqual(state['x_active'],state['x_picker']);self.assertEqual(state['x_active'],ids[6]);self.assertEqual(state['x_epoch'],1)
 def test_11_alternating_events_no_stale_explanation(self):
  rows=self.e;ids=[c['candidate_id'] for c in rows];state={};m.init_selection(state,'x',ids)
  for index in [0,8,25,1,17,3]:
   state['t']={'selection':{'rows':[index]}};m.table_changed(state,'x',ids,'t');c=next(c for c in rows if c['candidate_id']==state['x_active']);self.assertEqual(m.editorial(c)['source_quote_id'],rows[index]['quote_id'])
   state['x_picker']=ids[(index+1)%len(ids)];m.picker_changed(state,'x',ids);self.assertEqual(state['x_active'],ids[(index+1)%len(ids)])
 def test_12_document_namespaces_isolated(self):
  state={};e=[c['candidate_id'] for c in self.e];d=[c['candidate_id'] for c in self.d];m.init_selection(state,'e',e);m.init_selection(state,'d',d);state['e_picker']=e[3];m.picker_changed(state,'e',e);self.assertEqual(state['d_active'],d[0])
 def test_13_invalid_ID_or_row_rejected(self):
  ids=[c['candidate_id'] for c in self.e];s={};m.init_selection(s,'x',ids);s['x_picker']='BAD'
  with self.assertRaises(ValueError):m.picker_changed(s,'x',ids)
  s['t']={'selection':{'rows':[1000]}}
  with self.assertRaises(ValueError):m.table_changed(s,'x',ids,'t')
 def test_14_source_spans_after_any_selection(self):
  for doc in [m.core.verified_document('pil.502.pdf'),m.core.verified_document('050641Orig1s032lbl.pdf')]:
   for c in m.known(doc):self.assertEqual(doc['pages'][c['physical_page']-1]['text'][c['quote_start']:c['quote_end']],c['quote_exact'])
 def test_15_uncovered_LLMS_are_not_attached(self):
  c=next(c for c in self.d if c['name_tr']=='Glossit');self.assertEqual(m.explanation(c,'050641Orig1s032lbl.pdf'),[])
 def test_16_audit110_groups_and_no_scores_generated(self):
  a=m.core.read(m.core.ROOT/'reports/qa/WP13/v1_2/blind_audit.json');self.assertEqual(len(a['fold_checks']),110)
  for r in a['fold_checks']:self.assertTrue(r['drug_disjoint'] and r['group_disjoint'] and r['transform_train_only'] and r['target_train_only'])
  self.assertFalse(a['new_prediction']);self.assertFalse(a['new_model_fit'])
 def test_17_own_fold_demo_drugs_never_fit(self):
  a=m.core.read(m.core.ROOT/'reports/qa/WP13/v1_2/blind_audit.json')
  for r in a['example_checks']:self.assertTrue(r['in_outer_test']);self.assertFalse(r['in_own_model_train'] or r['in_train_graph'] or r['in_transform_fit'])
 def test_18_external_scope_blocked(self):
  a=m.core.read(m.core.ROOT/'reports/qa/WP13/v1_2/blind_audit.json');self.assertEqual(a['external_status'],'BLOCKED_NO_APPROVED_EXTERNAL_INPUT_ADAPTER')
if __name__=='__main__':unittest.main(verbosity=2)
