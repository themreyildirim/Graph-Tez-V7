import sys,unittest,json,copy,tempfile,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp13_tedizolid_B1_external_v1 as m
class Precommit(unittest.TestCase):
 def test_01_precommit_hashes(self):self.assertEqual(len(m.verify_precommit()['models']),5)
 def test_02_identity_and_units(self):
  x=m.read(m.Q/'active_input.json');m.validate_input(x);self.assertEqual(x['drug_id'],'DB14569');self.assertEqual(x['features']['HBA'],7)
 def test_03_references_rejected(self):
  x=m.read(m.Q/'active_input.json')
  for field in ['SIDER_labels','PDF_adverse_reactions','PT_frequency','reference']:
   z=copy.deepcopy(x);z[field]=[1]
   with self.assertRaisesRegex(ValueError,'INPUT_FIELD'):m.validate_input(z)
 def test_04_wrong_drug(self):
  x=m.read(m.Q/'active_input.json');x['drug_id']='DB09042'
  with self.assertRaisesRegex(ValueError,'REPRESENTATION'):m.validate_input(x)
 def test_05_feature_order(self):
  x=m.read(m.Q/'active_input.json');x['features']=dict(reversed(list(x['features'].items())))
  with self.assertRaisesRegex(ValueError,'ORDER'):m.validate_input(x)
 def test_06_wrong_units(self):
  x=m.read(m.Q/'active_input.json');x['units'][0]='kg/mol'
  with self.assertRaisesRegex(ValueError,'UNITS'):m.validate_input(x)
 def test_07_nonfinite(self):
  x=m.read(m.Q/'active_input.json');x['features']['MW']=float('nan')
  with self.assertRaisesRegex(ValueError,'NONFINITE'):m.validate_input(x)
 def test_08_rank_tie_CUI(self):self.assertEqual(m.rank_frame(['C2','C1'],np.array([.3,.3])).class_id.tolist(),['C1','C2'])
 def test_09_bad_scores_and_duplicate_target(self):
  for ids,s in [(['C1'],np.array([np.nan])),(['C1'],np.array([1.2])),(['C1','C1'],np.array([.2,.4]))]:
   with self.assertRaises(ValueError):m.rank_frame(ids,s)
 def test_10_equal_weight_score_mean(self):
  common=[f'C{i:04d}' for i in range(201)];frames=[m.rank_frame(common,np.full(201,v)) for v in [.1,.2,.3,.4,.5]]
  summary,matrix=m.common_summary(frames,common);self.assertTrue(np.allclose(summary.record_ranking_score,.3));self.assertEqual(matrix.shape,(201,5))
 def test_11_no_missing_target_filling(self):
  common=[f'C{i:04d}' for i in range(201)];frames=[m.rank_frame(common,np.full(201,.2)) for _ in range(5)];frames[0]=frames[0].iloc[:-1]
  with self.assertRaises(KeyError):m.common_summary(frames,common)
 def test_12_no_logit_mean_substitution(self):self.assertNotAlmostEqual(float(np.mean(expit([-5.,1.]))),float(expit(np.mean([-5.,1.]))),places=3)
 def test_13_mutation_hash_guard(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'input.txt';p.write_text('first');h=m.public_sha(p);p.write_text('mutated')
   with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):m.check_hashes({'input.txt':h},Path(d))
 def test_14_five_primary_and_common201(self):
  p=m.read(m.Q/'precommit_manifest.json');self.assertEqual([len(x['classes']) for x in p['models']],[220,262,267,270,275]);self.assertEqual([x['fold'] for x in p['models']],[1,2,3,4,5]);self.assertTrue(all(x['job'].startswith('primary_') for x in p['models']))
 def test_15_training_and_scaler_identity_exclusion(self):
  for model in m.read(m.Q/'precommit_manifest.json')['models']:
   meta=m.read(m.ROOT/model['model_json']);self.assertNotIn('DB14569',meta['train_drug_ids']);self.assertNotIn('DB14569',meta['transform_fit_sources']['chemistry_fit_drug_ids'])
 def test_16_old_replay_unchanged(self):
  r=pd.read_csv(m.PREP/'B1_heldout_replay.csv');self.assertEqual(sum(r.status.eq('PARITY_PASS')),108);self.assertEqual(sum(r.status.eq('ABSTAIN')),16)
if __name__=='__main__':unittest.main(verbosity=2)
