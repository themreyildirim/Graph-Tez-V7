"""Yalnız RAM'deki TECHNICAL_TEST_FIXTURE kayıtları;PDF veya prospektüs değildir."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_document_contract as c


def fixture():
    raw=b'TECHNICAL_TEST_BYTES_NOT_A_PDF';digest=c.sha256_bytes(raw);doc=c.document_id_for(digest);options={'technical_option':False}
    run=c.run_id_for(doc,'TEST_ONLY_NO_ENGINE','TEST_ONLY',options);text='TEST_ONLY A😀 ç\r\nİe\u0301 Z';textsha=c.text_digest(text);page=c.page_id_for(doc,run,0,textsha);start=text.index('😀');end=text.index('İ')+1;quote=text[start:end]
    return {'schema_version':c.VERSION,'data_status':'technical_test_fixture',
      'documents':[{'document_id':doc,'raw_sha256':digest,'raw_size_bytes':len(raw),'mime_type':'application/pdf','declared_version':None,'page_count':2,'receipts':[{'receipt_id':'TEST_ONLY_RECEIPT','source_kind':'user_provided_pdf','receipt_kind':'user_attachment','reference':'TEST_ONLY_NO_ATTACHMENT_EXISTS','original_filename':'TEST_ONLY_NOT_A_REAL_DOCUMENT.pdf','supplied_at':'2000-01-01T00:00:00Z'}]}],
      'extraction_runs':[{'extraction_run_id':run,'document_id':doc,'extractor_name':'TEST_ONLY_NO_ENGINE','extractor_version':'TEST_ONLY','extractor_options':options,'created_at':'2000-01-01T00:00:00+00:00','status':'partial'}],
      'pages':[{'page_id':page,'document_id':doc,'extraction_run_id':run,'page_index':0,'page_number':1,'printed_page_label':None,'text':text,'text_sha256':textsha,'text_length_codepoints':len(text),'text_status':'text_extracted'}],
      'quotes':[{'quote_id':c.quote_id_for(page,start,end,c.text_digest(quote)),'document_id':doc,'extraction_run_id':run,'page_id':page,'page_number':1,'char_start':start,'char_end':end,'quote':quote,'quote_sha256':c.text_digest(quote),'claim_kind':'verbatim_source_quote'}]}


class DocumentContractTests(unittest.TestCase):
    def validate(self,b):return c.validate_bundle(b,allow_test_fixtures=True)
    def test_01_waiting_registry_really_empty(self):
        self.assertEqual(c.validate_bundle(c.empty_bundle()),{'documents':0,'extraction_runs':0,'pages':0,'quotes':0,'data_status':'awaiting_user_pdfs'})
    def test_02_fixture_cannot_enter_real_registry(self):
        with self.assertRaises(ValueError):c.validate_bundle(fixture())
        self.assertEqual(self.validate(fixture())['quotes'],1)
    def test_03_document_identity_is_exact_content_hash(self):
        a=c.sha256_bytes(b'A');b=c.sha256_bytes(b'A ');self.assertNotEqual(c.document_id_for(a),c.document_id_for(b))
        x=fixture();x['documents'][0]['document_id']=c.document_id_for(b)
        with self.assertRaises(ValueError):self.validate(x)
    def test_04_duplicate_content_uses_receipt_aliases(self):
        b=fixture();receipt=copy.deepcopy(b['documents'][0]['receipts'][0]);receipt['receipt_id']='TEST_ONLY_SECOND_RECEIPT';receipt['original_filename']='TEST_ONLY_RENAMED.pdf';b['documents'][0]['receipts'].append(receipt)
        self.assertEqual(self.validate(b)['documents'],1)
        b['documents'].append(copy.deepcopy(b['documents'][0]))
        with self.assertRaises(ValueError):self.validate(b)
    def test_05_reject_automatic_source_and_URL(self):
        for field,value in [('source_kind','automatic_web_search'),('reference','https://example.invalid/NOT_A_DOCUMENT.pdf')]:
            b=fixture();b['documents'][0]['receipts'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.validate(b)
    def test_06_original_filename_is_not_a_path(self):
        for name in ['C:\\unprovided\\TEST_ONLY.pdf','../TEST_ONLY.pdf','TEST_ONLY.txt']:
            b=fixture();b['documents'][0]['receipts'][0]['original_filename']=name
            with self.subTest(name=name),self.assertRaises(ValueError):self.validate(b)
    def test_07_timezone_and_unique_receipt_required(self):
        b=fixture();b['documents'][0]['receipts'][0]['supplied_at']='2000-01-01T00:00:00'
        with self.assertRaises(ValueError):self.validate(b)
        b=fixture();b['documents'][0]['receipts']*=2
        with self.assertRaises(ValueError):self.validate(b)
    def test_08_run_config_identity_is_order_invariant_but_version_sensitive(self):
        d=c.document_id_for(c.sha256_bytes(b'TEST'))
        a=c.run_id_for(d,'TEST','v1',{'b':1,'a':2});self.assertEqual(a,c.run_id_for(d,'TEST','v1',{'a':2,'b':1}));self.assertNotEqual(a,c.run_id_for(d,'TEST','v2',{'a':2,'b':1}))
        b=fixture();b['extraction_runs'][0]['extractor_options']['changed']=True
        with self.assertRaises(ValueError):self.validate(b)
    def test_09_run_document_foreign_key(self):
        b=fixture();b['extraction_runs'][0]['document_id']=c.document_id_for('0'*64)
        with self.assertRaises(ValueError):self.validate(b)
    def test_10_physical_and_printed_page_numbers_separate(self):
        b=fixture();b['pages'][0]['printed_page_label']='iv';self.validate(b);b['pages'][0]['page_number']=4
        with self.assertRaises(ValueError):self.validate(b)
    def test_11_page_bounds_and_inspection_required(self):
        b=fixture();b['documents'][0]['page_count']=None
        with self.assertRaises(ValueError):self.validate(b)
        b=fixture();b['pages'][0]['page_index']=2;b['pages'][0]['page_number']=3
        with self.assertRaises(ValueError):self.validate(b)
    def test_12_exact_text_hash_forbids_silent_normalization(self):
        for change in [lambda s:s.replace('\r\n','\n'),lambda s:s.replace('e\u0301','é'),lambda s:s.strip()+' ']:
            b=fixture();b['pages'][0]['text']=change(b['pages'][0]['text'])
            with self.assertRaises(ValueError):self.validate(b)
    def test_13_unicode_codepoint_span_not_utf8_or_utf16(self):
        b=fixture();p=b['pages'][0];q=b['quotes'][0];self.assertEqual(q['quote'],p['text'][q['char_start']:q['char_end']]);self.validate(b)
        self.assertNotEqual(len(q['quote']),len(q['quote'].encode('utf-8')));q['char_end']+=1
        with self.assertRaises(ValueError):self.validate(b)
    def test_14_invalid_ranges_and_bool_offsets_rejected(self):
        for start,end in [(-1,2),(2,2),(3,2),(0,999),(True,2)]:
            b=fixture();b['quotes'][0].update(char_start=start,char_end=end)
            with self.subTest(start=start,end=end),self.assertRaises(ValueError):self.validate(b)
    def test_15_quote_must_equal_source_not_paraphrase(self):
        b=fixture();b['quotes'][0]['quote']='TEST_ONLY_PARAPHRASE'
        with self.assertRaises(ValueError):self.validate(b)
    def test_16_quote_cannot_jump_pages(self):
        b=fixture();b['quotes'][0]['page_number']=2
        with self.assertRaises(ValueError):self.validate(b)
    def test_17_page_text_revision_invalidates_old_quote(self):
        b=fixture();p=b['pages'][0];p['text']+=' TEST_ONLY_CHANGE';p['text_length_codepoints']=len(p['text']);p['text_sha256']=c.text_digest(p['text']);p['page_id']=c.page_id_for(p['document_id'],p['extraction_run_id'],p['page_index'],p['text_sha256'])
        with self.assertRaises(ValueError):self.validate(b)
    def test_18_duplicate_page_quote_ids_rejected(self):
        for key in ['pages','quotes']:
            b=fixture();b[key].append(copy.deepcopy(b[key][0]))
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(b)
    def test_19_no_text_page_can_be_preserved_without_fake_quote(self):
        b=fixture();p=b['pages'][0];p['text']='';p['text_length_codepoints']=0;p['text_sha256']=c.text_digest('');p['text_status']='no_text';p['page_id']=c.page_id_for(p['document_id'],p['extraction_run_id'],0,p['text_sha256']);b['quotes']=[];self.validate(b)
        p['text_status']='text_extracted'
        with self.assertRaises(ValueError):self.validate(b)
    def test_20_complete_run_requires_all_pages_including_blank(self):
        b=fixture();b['extraction_runs'][0]['status']='complete'
        with self.assertRaises(ValueError):self.validate(b)
        p=copy.deepcopy(b['pages'][0]);p.update(page_index=1,page_number=2,text='',text_length_codepoints=0,text_sha256=c.text_digest(''),text_status='no_text');p['page_id']=c.page_id_for(p['document_id'],p['extraction_run_id'],1,p['text_sha256']);b['pages'].append(p);self.validate(b)
    def test_21_model_claims_and_unknown_columns_not_source_quotes(self):
        for key,value in [('predicted_by_GNN',.5),('kalite_skoru',1),('clinical_risk',.8)]:
            b=fixture();b['quotes'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(b)
    def test_22_nonfinite_options_and_mutation_rejected(self):
        b=fixture();before=copy.deepcopy(b);self.validate(b);self.assertEqual(b,before);b['extraction_runs'][0]['extractor_options']['bad']=float('nan')
        with self.assertRaises(ValueError):self.validate(b)
    def test_23_extract_gate_opens_no_files(self):
        with patch('builtins.open',side_effect=AssertionError('No PDF access')):
            c.validate_bundle(c.empty_bundle())
            with self.assertRaises(c.AwaitingUserPDFError):c.extract_user_pdfs('UNSUPPLIED_TEST_PATH.pdf')
    def test_24_exported_schema_matches_implemented_contract(self):
        p=Path(__file__).resolve().parents[1]/'docs/schemas/WP12_document_bundle_v1.schema.json';self.assertEqual(json.loads(p.read_text(encoding='utf-8')),c.schema())
        b=fixture();b['data_status']='awaiting_user_pdfs'
        with self.assertRaises(ValueError):self.validate(b)


if __name__=='__main__':unittest.main(verbosity=2)
