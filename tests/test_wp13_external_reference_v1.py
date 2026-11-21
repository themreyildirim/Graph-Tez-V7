"""Frozen-artifact / source-range / scope separation checks, no model runs."""
import ast
import hashlib
import json
import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import wp13_external_reference_v1 as r

class ReferenceTests(unittest.TestCase):
    def test_01_original_locks_and_all_source_pins(self):r.verify_locks()
    def test_02_preserved_prior_files(self):r.verify_pins(r.read(r.Q/'prior_pins.json'))
    def test_03_pdf_copy_equals_user_original(self):
        m=r.read(r.Q/'document_metadata.json');self.assertEqual(r.sha(r.PDF),m['raw_sha256']);self.assertEqual(r.sha(r.Q/'reference'/r.PDF.name),m['raw_sha256'])
    def test_04_all_physical_pages_and_text_hashes(self):
        p=r.read(r.Q/'pages.json');self.assertEqual([x['physical_page'] for x in p],list(range(1,16)))
        for x in p:self.assertEqual(hashlib.sha256(x['text'].encode()).hexdigest(),x['text_sha256']);self.assertTrue(x['text'].strip())
    def test_05_every_quote_exact_range(self):
        p=r.read(r.Q/'pages.json');qs=[t['quote'] for t in r.read(r.Q/'reference_terms.json')]+r.read(r.Q/'context_quotes.json')+r.read(r.Q/'complete_4_8_pages.json')
        for q in qs:
            self.assertEqual(p[q['physical_page']-1]['text'][q['char_start']:q['char_end']],q['quote_exact'])
            self.assertEqual(hashlib.sha256(q['quote_exact'].encode()).hexdigest(),q['quote_sha256'])
    def test_06_all_table_cells(self):
        terms=r.read(r.Q/'reference_terms.json');self.assertEqual(len(terms),76);self.assertEqual(len(set(t['term_tr'] for t in terms)),76)
        self.assertEqual({6,7,8},{t['quote']['physical_page'] for t in terms})
    def test_07_frequency_column_not_text_order(self):
        d={t['term_tr']:t for t in r.read(r.Q/'reference_terms.json')}
        self.assertEqual(d['Diyare']['frequency'],'Yaygın');self.assertEqual(d['Karın ağrısı']['frequency'],'Yaygın olmayan')
        self.assertEqual(d['Genel prürit']['frequency'],'Yaygın');self.assertEqual(d['Prürit']['frequency'],'Yaygın olmayan')
        self.assertEqual(sum(t['frequency']=='Yaygın' for t in d.values()),7)
    def test_08_table_geometry_reproducible(self):self.assertEqual(r.extract_reference_terms(),r.read(r.Q/'reference_terms.json'))
    def test_09_scores_and_order_identical(self):
        a=pd.read_csv(r.P/'common201_scores.csv',float_precision='round_trip');b=pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip')
        pd.testing.assert_frame_equal(a,b[a.columns]);self.assertEqual(len(b),201)
    def test_10_all_five_model_scores_exact(self):
        a=pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip').set_index('class_id')
        for i in range(1,6):
            b=pd.read_csv(r.P/f'fold{i}_scores.csv',float_precision='round_trip').set_index('class_id')
            np.testing.assert_array_equal(a[f'fold{i}_score'].values,b.loc[a.index,'record_ranking_score'].values)
    def test_11_common_mean_not_logit_ensemble(self):
        a=pd.read_csv(r.Q/'comparison201.csv',float_precision='round_trip');np.testing.assert_allclose(a.record_ranking_score,a[[f'fold{i}_score' for i in range(1,6)]].mean(axis=1),rtol=0,atol=1e-15)
    def test_12_top10_preselected_not_reference_selected(self):
        a=r.read(r.Q/'top10_comparison.json');b=r.read(r.S/'selected_PT_names.json');self.assertEqual([x['class_id'] for x in a],[x['class_id'] for x in b])
    def test_13_human_pending_and_no_expert_confirmed(self):
        for a in r.read(r.Q/'comparison201.json'):self.assertEqual(a['human_review'],'PENDING');self.assertFalse(a['expert_confirmed_equivalent']);self.assertFalse(a['reference_absence_is_negative'])
    def test_14_no_shock_from_hypersensitivity(self):
        a={x['class_id']:x for x in r.read(r.Q/'comparison201.json')};self.assertEqual(a['C0002792']['mapping_status'],'UNMAPPED');self.assertIn('İlaca aşırı duyarlılık',a['C0020517']['source_terms'])
    def test_15_thrombocytopenia_class_not_product_table(self):
        a=[x for x in r.read(r.Q/'crosswalk_candidates.json') if x['class_id']=='C0040034'];self.assertFalse(any(x['source_channel']=='4.8_TABLE' for x in a))
        self.assertTrue(any(x['source_channel']=='4.4_CLASS_WARNING' for x in a));self.assertTrue(any(x['relation']=='RELATED_DISTINCT' for x in a))
    def test_16_gi_and_abdominal_targets_not_merged(self):
        a={x['class_id']:x for x in r.read(r.Q/'comparison201.json')};self.assertNotEqual(a['C0687713']['reference_status'],a['C0000737']['reference_status']);self.assertNotEqual(a['C0687713']['class_id'],a['C0000737']['class_id'])
    def test_17_overdose_animal_contraindication_separate(self):
        terms=r.read(r.Q/'reference_terms.json');self.assertTrue(all(t['scope']=='PRODUCT_POOLED_ORAL_IV' for t in terms))
        scopes={q['statement_kind'] for q in r.read(r.Q/'context_quotes.json')};self.assertTrue({'overdose','preclinical','contraindication'}.issubset(scopes))
    def test_18_product_identity_not_molecular_equivalence(self):
        a=r.read(r.Q/'product_identity_and_limitations.json');self.assertEqual(a['model_input'],'DB14569 active TEDIZOLID');self.assertEqual(a['ingredient'],'tedizolid fosfat');self.assertEqual(a['clinical_product_equivalence'],'NOT_ESTABLISHED');self.assertEqual(a['DB09042_prediction'],'NOT_RUN')
    def test_19_currentness_not_pdf_creation_date(self):
        a=r.read(r.Q/'product_identity_and_limitations.json');self.assertEqual(a['currentness'],'NOT_VERIFIED');self.assertIn('NOT_STATED',a['KUB_revision_date'])
    def test_20_all_crosswalk_refs_resolve(self):
        ts=r.read(r.Q/'reference_terms.json');ctx=r.read(r.Q/'context_quotes.json');ids={x['quote']['quote_id'] for x in ts}|{x['quote_id'] for x in ctx}
        for x in r.read(r.Q/'crosswalk_candidates.json'):self.assertIn(x['quote_id'],ids);self.assertEqual(x['human_review'],'PENDING');self.assertEqual(x['status'],'PROVISIONAL')
    def test_21_summary_counts_and_metrics_na(self):
        a=r.read(r.Q/'comparison_summary.json');self.assertEqual(a['top10_status_counts'],{'TABLE_TRANSLATION_CANDIDATE':6,'TABLE_RELATED_NOT_EQUIVALENT':2,'NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE':1,'CLASS_WARNING_ONLY':1});self.assertIsNone(a['clinical_success_rate']);self.assertEqual(a['performance_metrics'],'NOT_CALCULABLE')
    def test_22_saved_shap_50_300_no_ensemble(self):
        self.assertEqual(len(r.read(r.S/'pair_additivity.json')),50);self.assertEqual(len(r.read(r.S/'local_feature_SHAP.json')),300);self.assertTrue(r.read(r.S/'explanation_lock.json')['no_ensemble_SHAP'])
    def test_23_ui_pt_fold_alignment_all50(self):
        v=r.read(r.S/'Turkish_verbal_explanations.json');p=r.read(r.S/'pair_additivity.json');self.assertEqual({(x['class_id'],x['fold']) for x in v},{(x['class_id'],x['fold']) for x in p});self.assertEqual(len(v),50)
    def test_24_ui_hash_pins(self):r.verify_pins(r.read(r.Q/'presentation_pins.json'))
    def test_25_no_model_or_network_calls_in_new_reference_modules(self):
        for n in ['wp13_external_reference_v1.py','wp13_external_reference_ui_v1.py']:
            tree=ast.parse((ROOT/'scripts'/n).read_text(encoding='utf-8'))
            for a in ast.walk(tree):
                if isinstance(a,ast.Call) and isinstance(a.func,ast.Attribute):self.assertNotIn(a.func.attr,{'predict','predict_proba','forward','fit','backward','post','urlopen','exact_phi_base'})
    def test_26_wrong_quote_range_rejected(self):
        with self.assertRaises(AssertionError):r.quote(7,'Diyare','adverse','product',0)
    def test_27_no_crosswalk_approval_or_negative_labels(self):
        text=(r.Q/'comparison201.csv').read_text(encoding='utf-8-sig');self.assertNotIn('VERIFIED_MATCH',text);self.assertNotIn('TRUE_NEGATIVE',text)
    def test_28_timestamps_before_reference_and_no_trusted_clock_claim(self):
        from datetime import datetime
        a=r.read(r.Q/'before_reference_checks.json');b=r.read(r.Q/'document_metadata.json')
        self.assertLess(datetime.fromisoformat(a['prediction_created_utc']),datetime.fromisoformat(a['explanation_created_utc']))
        self.assertLess(datetime.fromisoformat(a['explanation_created_utc']),datetime.fromisoformat(b['source_receipt_utc']))
        self.assertIn('not an independent trusted timestamp',a['timing_scope'])
    def test_29_current_app_additive_prior_entry_unchanged(self):
        pin=r.read(r.Q/'prior_pins.json')['apps/drug_safety_explorer_FINAL_v2.py'];self.assertEqual(r.sha(ROOT/'apps/drug_safety_explorer_FINAL_v2.py'),pin);self.assertTrue((ROOT/'apps/drug_safety_explorer_FINAL_v3.py').exists())
    def test_30_cross_page_class_scope_bridge(self):
        q=r.read(r.Q/'class_scope_bridge.json');raw=r.read(r.Q/'pages.json')[1]['text'];self.assertEqual(raw[q['char_start']:q['char_end']],q['quote_exact']);self.assertIn('Oksazolidinon sınıfının',q['quote_exact'])
    def test_31_all50_linked_verbal_and_score_unchanged(self):
        linked=r.read(r.Q/'model_reference_explanations50.json');original=r.read(r.S/'Turkish_verbal_explanations.json');top={x['class_id']:x for x in r.read(r.Q/'top10_comparison.json')}
        self.assertEqual(len(linked),50)
        for a,b in zip(linked,original):
            self.assertEqual(a['explanation_tr'],b['explanation_tr']);self.assertEqual(a['locked_model_score'],top[a['class_id']]['fold'+str(a['fold'])+'_score'])
    def test_32_executed_notebook_no_errors(self):
        n=r.read(ROOT/'notebooks/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb');cells=[c for c in n['cells'] if c['cell_type']=='code'];self.assertEqual([c['execution_count'] for c in cells],list(range(1,6)))
        self.assertTrue(all(c['outputs'] for c in cells));self.assertFalse(any(o['output_type']=='error' for c in cells for o in c['outputs']))
    def test_33_real_browser_screen_files(self):
        shots=list((r.F/'screenshots').glob('0[2-7]*.jpg'));self.assertEqual(len(shots),6)
        for p in shots:self.assertEqual(p.read_bytes()[:2],b'\xff\xd8');self.assertGreater(p.stat().st_size,10000)
    def test_34_streamlit_widget_checks(self):
        x=r.read(r.Q/'Streamlit_AppTest_results.json');self.assertEqual(len(x['checks']),7);self.assertTrue(all(t['status']=='PASS' for t in x['checks']));self.assertFalse(x['model_execution'])
    def test_35_hash_mismatch_stops_before_reference_read(self):
        from unittest.mock import patch
        with patch.object(r,'sha',return_value='0'*64),patch.object(r,'read',side_effect=AssertionError('read must not be reached')):
            with self.assertRaisesRegex(ValueError,'PREDICTION_LOCK_MISMATCH_STOP'):r.verify_locks()
    def test_36_human_template_pending(self):
        x=pd.read_csv(r.Q/'human_review_TEMPLATE.csv');self.assertEqual(len(x),10)
        for c in ['terminology_equivalence','product_scope_appropriateness','frequency_interpretation','final_human_decision','reviewer','reviewed_at']:self.assertEqual(set(x[c]),{'PENDING'})

if __name__=='__main__':unittest.main(verbosity=2)
