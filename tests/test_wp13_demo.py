import unittest,sys,tempfile,json,socket
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_core as c
import wp13_api as api
import wp13_api_budget as b

class Demo(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=c.verified_document('pil.502.pdf');cls.d=c.verified_document('050641Orig1s032lbl.pdf')
 def test_01_source_hashes_pages_and44_quotes(self):
  self.assertEqual((self.e['page_count'],self.d['page_count']),(6,11));self.assertEqual(len(self.e['quotes'])+len(self.d['quotes']),44)
 def test_02_quote_ranges(self):
  for doc in [self.e,self.d]:
   for q in doc['quotes']:self.assertEqual(doc['pages'][q['page_number']-1]['text'][q['char_start']:q['char_end']],q['quote'])
 def test_03_wrong_parent_rejected(self):
  with self.assertRaisesRegex(ValueError,'IDENTITY_MISMATCH'):c.match_upload((c.ROOT/'data/user_pdfs/pil.502.pdf').read_bytes(),'DB00254')
 def test_04_unknown_upload_not_name_matched(self):self.assertIsNone(c.match_upload(b'%PDF-UNKNOWN_TEST_FIXTURE'))
 def test_05_invalid_pdf(self):
  with self.assertRaises(ValueError):c.extract_pdf(b'not PDF')
 def test_06_blank_pdf_no_ADR(self):
  with c.get_engine().open() as d:d.new_page();data=d.tobytes()
  doc=c.extract_pdf(data);self.assertEqual(doc['pages'][0]['status'],'NO_TEXT');self.assertEqual(c.candidates(doc),[])
 def test_07_image_only_pdf_no_OCR(self):
  e=c.get_engine()
  with e.open() as d:
   page=d.new_page();pix=e.Pixmap(e.csRGB,e.IRect(0,0,2,2),False);pix.clear_with(255);page.insert_image(e.Rect(0,0,40,40),pixmap=pix);data=d.tobytes()
  doc=c.extract_pdf(data);self.assertEqual(doc['pages'][0]['status'],'IMAGE_TEXT_UNAVAILABLE');self.assertEqual(c.candidates(doc),[]);self.assertFalse(doc['OCR'])
 def test_08_Doxy_page10_footer_not_box(self):self.assertEqual(self.d['pages'][9]['status'],'IMAGE_TEXT_UNAVAILABLE')
 def test_09_experimental_keyword_window_is_exact(self):
  doc=c.extract_pdf((c.ROOT/'data/user_pdfs/pil.502.pdf').read_bytes());q=c.candidates(doc)[0]
  self.assertEqual(q['status'],'EXPERIMENTAL');self.assertEqual(q['quote'],doc['pages'][q['physical_page']-1]['text'][q['char_start']:q['char_end']])
 def test_10_upload_gnn_not_available(self):self.assertEqual(c.gnn({'mode':'EXPERIMENTAL_UPLOAD'})['status'],'NOT_AVAILABLE')
 def test_11_gnn_real_scope(self):
  for doc,count in [(self.e,318),(self.d,240)]:
   g=c.gnn(doc);self.assertEqual(g['targets'],count);self.assertEqual(len({x['class_id'] for x in g['rows']}),count)
 def test_12_gnn_missing_artifact_no_fallback(self):
  with patch.object(c,'pinned',side_effect=ValueError('MISSING')):self.assertEqual(c.gnn(self.e)['status'],'NOT_AVAILABLE')
 def test_13_saved_explanations_pending(self):
  self.assertTrue(all(x['human_decision']=='PENDING' for x in c.saved_explanations('pil.502.pdf')))
 def test_14_budget_old_and_projected(self):
  p=b.prior.base.old.c.read(b.prior.base.POLICY);v=b.aggregate(p);self.assertEqual((v['HTTP_reservations_total'],v['inference_reservations_total'],v['reserved_USD']),(18,6,'0.138'));self.assertEqual(b.projected(p,HTTP=3,inference=1)['reserved_USD'],'0.161');self.assertFalse(b.projected(p,HTTP=13)['within_limits'])
 def test_15_consent_gate_before_host_key_or_network(self):
  with patch.object(api,'project_key',side_effect=AssertionError('NO_KEY_READ')),patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK')):self.assertEqual(api.run_from_ui('pil.502.pdf',False)['status'],'EXPLICIT_CONSENT_REQUIRED')
 def test_16_appcontainer_gate(self):
  with patch.object(api.old,'is_appcontainer',return_value=True),patch.object(api,'project_key',side_effect=AssertionError('NO_KEY_READ')):self.assertEqual(api.run_from_ui('pil.502.pdf',True)['status'],'APPCONTAINER_STOP_NO_API')
 def test_17_API_one_attempt_no_repeat(self):
  p={**b.prior.base.old.c.read(b.prior.base.POLICY),'execution_scope_version':'TEST_ONLY'}
  with tempfile.TemporaryDirectory(dir=c.QA,prefix='TEST_ONLY_') as temp,patch.object(b,'CONTROL',Path(temp)/'control'),patch.object(b,'verify',return_value=p):
   folder=Path(temp)/'run';folder.mkdir();calls=[]
   def fail(*args):calls.append(1);raise TimeoutError()
   api.perform(folder,'TEST_ONLY_NOT_KEY',p,'S04',send=fail)
   folder2=Path(temp)/'second';folder2.mkdir();api.perform(folder2,'TEST_ONLY_NOT_KEY',p,'S07',send=fail)
   self.assertEqual(len(calls),1)

 def test_18_altered_quote_range_rejected(self):
  from copy import deepcopy
  original=c.read
  def changed(path):
   data=original(path)
   if Path(path).name=='source_evidence_bundle.json':
    data=deepcopy(data);data['quotes'][0]['char_start']+=1
   return data
  with patch.object(c,'read',side_effect=changed):
   with self.assertRaisesRegex(ValueError,'QUOTE_RANGE_MISMATCH'):c.verified_document('pil.502.pdf')
 def test_19_secret_echo_blocked(self):
  from wp12_api_security import Evidence,SecretBlocked
  with tempfile.TemporaryDirectory(dir=c.QA,prefix='TEST_ONLY_') as temp:
   with self.assertRaises(SecretBlocked):Evidence(temp,'TEST_ONLY_SECRET').text('response.txt','TEST_ONLY_SECRET')
if __name__=='__main__':unittest.main(verbosity=2)
