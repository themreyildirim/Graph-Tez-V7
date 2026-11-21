import unittest,json,sys
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_b1_external_parity_v1 as m
class Preparation(unittest.TestCase):
 def test_01_both_outside_frozen_inventory(self):
  rows=json.loads((m.Q/'identity_vs_frozen62.json').read_text());self.assertEqual(len(rows),2);self.assertTrue(all(r['outside_frozen62'] for r in rows))
 def test_02_all_saved_train_IDs(self):
  rows=json.loads((m.Q/'frozen_model_training_identity_checks.json').read_text());self.assertEqual(len(rows),20);self.assertTrue(all(not r['tedizolid_overlap'] for r in rows))
 def test_03_structures_valid_and_different(self):
  d=pd.read_csv(m.Q/'chemical_QC_features.csv');self.assertTrue(d.parse_status.eq('valid').all());self.assertEqual(d.components.tolist(),[1,1]);self.assertEqual(d.rdkit_inchikey.nunique(),2);self.assertTrue((d.rdkit_inchikey==d.XML_InChIKey).all())
 def test_04_stereochemistry_no_invention(self):
  d=pd.read_csv(m.Q/'chemical_QC_features.csv');self.assertTrue(d.chiral_unassigned.eq(0).all());self.assertTrue(d.chiral_assigned.eq(1).all())
 def test_05_exact_feature_definitions(self):
  d=pd.read_csv(m.Q/'chemical_QC_features.csv').set_index('id');self.assertAlmostEqual(d.loc['DB14569','MW'],370.344,places=6);self.assertAlmostEqual(d.loc['DB09042','LogP'],1.5127,places=6);self.assertEqual(d.loc['DB09042','HBA'],8);self.assertTrue(d.TPSA_includeSandP.eq(False).all())
 def test_06_feature_order_guard(self):
  with self.assertRaisesRegex(ValueError,'ORDER'):m.transform({'LogP':1}, {}, True)
 def test_07_neutral_mask_not_fake_chemistry(self):self.assertTrue(np.array_equal(m.transform({}, {},False),np.zeros(6)))
 def test_08_external_score_hard_stop(self):
  for allowed in [{'DB00199'},{'DB14569'}]:
   with self.assertRaisesRegex(ValueError,'NOT_AUTHORIZED'):m.heldout_scores('DB14569',np.ones(6),{},allowed)
 def test_09_replay_no_refit(self):
  r=pd.read_csv(m.Q/'B1_heldout_replay.csv');self.assertEqual(len(r),124);self.assertTrue((r.transform_error<1e-12).all());self.assertTrue((r[r.status.eq('PARITY_PASS')].score_error<1e-12).all());self.assertEqual(set(r.status),{'PARITY_PASS','ABSTAIN'})
 def test_10_human_features_verified(self):
  d=pd.read_csv(m.Q/'human_protein_QA.csv');self.assertEqual(set(d.accession),{'P21397','P27338'});self.assertTrue(d.features56_present.all() and d.finite.all());self.assertTrue(d.taxid.eq(9606).all())
 def test_11_fold_specific_PPI_not_filled(self):
  d=pd.read_csv(m.Q/'fold_PPI_scope.csv');self.assertFalse(d[d.fold.eq(3)].in_frozen_train_proteins.any());self.assertTrue(d[d.fold.eq(3)].PPI700_incident_pairs.eq(0).all());self.assertTrue(d[~d.fold.eq(3)].PPI700_incident_pairs.eq(4).all())
 def test_12_bacterial_rRNA_not_protein(self):
  d=json.loads((m.Q/'DrugBank_identity_chemistry.json').read_text(encoding='utf-8'))
  for r in d:
   target=next(t for t in r['roles'] if t['role']=='targets');self.assertEqual(target['polypeptides'],[]);self.assertNotEqual(target['organism'],'Humans')
 def test_13_information_exposure_reported(self):
  d=json.loads((m.Q/'blindness_audit.json').read_text());self.assertTrue(d['incidental_search_safety_snippets_exposure']);self.assertFalse(d['SIDER_tedizolid_labels_accessed']);self.assertFalse(d['SIVEXTRO_PDF_opened']);self.assertEqual(d['external_scores'],0)
 def test_14_representation_not_automatically_committed(self):
  d=json.loads((m.Q/'model_policy_options.json').read_text());self.assertEqual(d['single_model_or_ensemble'],'PENDING_USER_APPROVAL');self.assertEqual(d['external_scoring'],'NOT_RUN')
if __name__=='__main__':unittest.main(verbosity=2)
