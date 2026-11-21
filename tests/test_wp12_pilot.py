"""Gerçek iki PDF'nin provenans/sayfa/aralık ve pilot bağlam doğrulaması."""
import copy,json,socket,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp12_pilot import ROOT,QA,SOURCE,FILES,read,preserve,get_engine
from wp12_prepare import sha
from wp12_document_contract import validate_bundle,text_digest,quote_id_for


class RealPDFPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=read(QA/'source_evidence_bundle.json');cls.ann=read(QA/'source_context_annotations.json');cls.q={q['quote_id']:q for q in cls.b['quotes']};cls.a={a['key']:a for a in cls.ann};cls.p={p['page_id']:p for p in cls.b['pages']};cls.engine=get_engine()

    def quote(self,key):return self.q[self.a[key]['quote_id']]

    def test_01_only_user_selected_sources_exist_and_hash_match(self):
        receipt=read(QA/'user_source_receipts.json');self.assertEqual([r['filename'] for r in receipt['records']],list(FILES));self.assertFalse(receipt['downloaded'])
        for d,r in zip(self.b['documents'],receipt['records']):
            path=SOURCE/r['filename'];self.assertTrue(path.is_file());self.assertEqual(sha(path),d['raw_sha256']);self.assertEqual(sha(path),r['raw_sha256']);self.assertEqual(path.stat().st_size,d['raw_size_bytes']);self.assertEqual(d['receipts'][0]['receipt_kind'],'explicit_user_file')

    def test_02_real_page_counts_and_pdf_format(self):
        self.assertEqual([d['page_count'] for d in self.b['documents']],[6,11])
        for f in FILES:
            with self.engine.open(str(SOURCE/f)) as pdf:self.assertTrue(pdf.is_pdf);self.assertFalse(pdf.needs_pass)

    def test_03_existing_contract_accepts_real_bundle(self):
        self.assertEqual(validate_bundle(self.b),{'documents':2,'extraction_runs':2,'pages':17,'quotes':44,'data_status':'user_pdf_records'})

    def test_04_all_pages_reextract_exactly_offline_no_subprocess(self):
        options=read(QA/'extraction_policy_before_run.json')['options'];self.assertFalse(options['OCR']);self.assertFalse(options['sort'])
        def forbidden(*a,**k):raise AssertionError('No network/process/model call allowed during text extraction')
        with patch.object(socket,'create_connection',forbidden),patch.object(socket.socket,'connect',forbidden),patch.object(subprocess,'Popen',forbidden):
            for d in self.b['documents']:
                with self.engine.open(str(SOURCE/d['receipts'][0]['original_filename'])) as pdf:
                    ps=[p for p in self.b['pages'] if p['document_id']==d['document_id']]
                    self.assertEqual([p['page_index'] for p in ps],list(range(len(pdf))))
                    for p in ps:
                        actual=pdf[p['page_index']].get_text('text',sort=False,flags=options['flags']);self.assertEqual(actual,p['text']);self.assertEqual(text_digest(actual),p['text_sha256'])
        self.assertNotIn('onnxruntime',sys.modules)

    def test_05_all_quote_spans_and_hashes_exact(self):
        for q in self.q.values():
            p=self.p[q['page_id']];self.assertEqual(q['quote'],p['text'][q['char_start']:q['char_end']]);self.assertEqual(q['quote_sha256'],text_digest(q['quote']));self.assertEqual(q['quote_id'],quote_id_for(q['page_id'],q['char_start'],q['char_end'],q['quote_sha256']))

    def test_06_user_requested_pages_and_section_boundaries(self):
        for key,page in [('E_adverse_p4',4),('E_adverse_p5',5),('D_adverse_all',7)]:self.assertEqual(self.quote(key)['page_number'],page)
        self.assertIn('4.  Possible side effects',self.quote('E_adverse_p4')['quote']);self.assertNotIn('How to take',self.quote('E_adverse_p4')['quote']);self.assertNotIn('OVERDOSAGE',self.quote('D_adverse_all')['quote'])

    def test_07_physical_vs_visible_printed_number(self):
        doc=self.b['documents'][1]
        ps=[p for p in self.b['pages'] if p['document_id']==doc['document_id']]
        for p in ps[:9]:self.assertEqual(p['printed_page_label'],f"Page {p['page_number']} of 9")
        self.assertIsNone(ps[9]['printed_page_label']);self.assertEqual(ps[10]['printed_page_label'],'Signature Page 1 of 1');self.assertEqual(ps[10]['page_number'],11)

    def test_08_image_package_page_not_dropped_or_invented_as_text(self):
        doc=self.b['documents'][1];p=next(p for p in self.b['pages'] if p['document_id']==doc['document_id'] and p['page_number']==10)
        self.assertEqual(len(p['text']),154);self.assertNotIn('150 mg',p['text']);self.assertTrue(any(n['physical_page']==10 and 'NO_OCR' in n['status'] for n in read(QA/'visual_content_notes.json')))
        self.assertTrue((ROOT/'reports/figures/WP12/pilot_v1/pages/doxycycline/page-10.png').is_file())

    def test_09_versions_confirmed_from_body_not_filesystem(self):
        self.assertIn('December 2025',self.quote('E_revision')['quote']);self.assertIn('Rev: 02/2022',self.quote('D_revision')['quote'])
        for r in read(QA/'document_metadata_content_review.json'):self.assertTrue(r['metadata_dates_are_not_document_revision']);self.assertFalse(r['latest_label_verified'])
        self.assertIn('may not be the latest approved by FDA',self.quote('D_latest_notice')['quote'])

    def test_10_class_scope_is_inherited_not_direct_doxycycline(self):
        intro=self.quote('D_class_intro');self.assertIn('patients receiving tetracyclines',intro['quote'])
        for suffix in ['GI','skin','renal','hypersensitivity','blood','other','thyroid']:
            a=self.a['D_class_'+suffix];self.assertEqual(a['attribution_scope'],'class_level');self.assertIn(intro['quote_id'],a['context_quote_ids'])

    def test_11_BUN_exception_preserves_both_sentences(self):
        q=self.quote('D_BUN_exception')['quote'];self.assertIn('tetracyclines may cause an increase in BUN',q);self.assertIn('does not occur',q);self.assertIn('doxycycline in patients with impaired renal function',q);self.assertEqual(self.a['D_BUN_exception']['attribution_scope'],'class_statement_with_doxycycline_exception')

    def test_12_direct_drug_statements_keep_qualifiers(self):
        self.assertEqual(self.a['D_direct_intro']['attribution_scope'],'drug_direct');self.assertIn('infrequent',self.quote('D_direct_intro')['quote']);self.assertIn('might increase',self.quote('D_direct_candidiasis')['quote'])

    def test_13_named_tetracycline_is_not_silently_doxycycline(self):
        q=self.quote('D_tetracycline_methoxyflurane')['quote'];self.assertIn('tetracycline and methoxyflurane',q);self.assertNotIn('doxycycline',q);self.assertEqual(self.a['D_tetracycline_methoxyflurane']['attribution_scope'],'other_named_drug_tetracycline')

    def test_14_existing_parent_salt_ID_mapping(self):
        identity=read(QA/'drug_identity_review.json');self.assertEqual([i['DrugBank_parent_id'] for i in identity],['DB00199','DB00254']);self.assertEqual(identity[1]['existing_salt_link_id'],'DBSALT001956');self.assertIsNone(identity[0]['existing_salt_link_id'])
        self.assertIn('doxycycline monohydrate',self.quote('D_identity')['quote']);self.assertIn('enteric-coated',self.quote('E_formulation')['quote'])
        for i in identity:self.assertEqual(i['mapping_level'],'active_ingredient_parent');self.assertEqual(i['product_or_dose_equivalence'],'NOT_ESTABLISHED_NOT_USED_IN_MODEL')

    def test_15_no_model_labels_or_inputs_generated(self):
        for a in self.ann:self.assertFalse(a['is_training_label']);self.assertFalse(a['is_model_input']);self.assertEqual(a['review_status'],'PILOT_SOURCE_CONTEXT_REVIEW_USER_REVIEW_PENDING')
        for q in self.q.values():self.assertEqual(q['claim_kind'],'verbatim_source_quote');self.assertNotIn('meddra_cui',q);self.assertNotIn('predicted_by_GNN',q)

    def test_16_previous_models_reports_QA_and_pdfs_unchanged(self):self.assertEqual(preserve(),3208)

    def test_17_actual_quote_tamper_is_rejected(self):
        b=copy.deepcopy(self.b);b['quotes'][0]['char_end']+=1
        with self.assertRaises(ValueError):validate_bundle(b)
        b=copy.deepcopy(self.b);b['quotes'][0]['quote']='NOT_THE_SOURCE'
        with self.assertRaises(ValueError):validate_bundle(b)

    def test_18_text_files_preserve_exact_UTF8_and_all_pages_rendered(self):
        for d in self.b['documents']:
            name=d['receipts'][0]['original_filename'];folder='erythromycin' if name==FILES[0] else 'doxycycline'
            self.assertEqual(len(list((ROOT/'reports/figures/WP12/pilot_v1/pages'/folder).glob('page-*.png'))),d['page_count'])
            for p in self.b['pages']:
                if p['document_id']==d['document_id']:
                    raw=(QA/'page_text'/(name+f".page_{p['page_number']:03}.txt")).read_bytes();self.assertEqual(raw,p['text'].encode('utf-8'))


if __name__=='__main__':unittest.main(verbosity=2)
