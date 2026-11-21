"""Salt okunur teslim regresyonları. Fit, model forward veya SHAP hesabı çalıştırılmaz."""
import csv,json,hashlib,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'EMT2_Teslim_v1';Q=R/'reports/qa/WP13'
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
class Teslim(unittest.TestCase):
 def test_rank_is_locked_mean_not_probability_label(self):
  table=rows(Q/'WP13_EXTERNAL_REFERENCE_COMPARISON_v1/comparison201.csv')
  self.assertEqual(len(table),201);self.assertEqual([int(x['rank']) for x in table],list(range(1,202)))
  self.assertEqual([x['class_id'] for x in table[:10]],[x['class_id'] for x in rows(Q/'WP13_EXTERNAL_REFERENCE_COMPARISON_v1/top10_comparison.csv')])
  for x in table:
   self.assertEqual(x['drug_id'],'DB14569');self.assertAlmostEqual(sum(float(x[f'fold{i}_score']) for i in range(1,6))/5,float(x['record_ranking_score']),places=13)
 def test_missing_reference_is_not_negative(self):
  x=next(x for x in rows(Q/'WP13_EXTERNAL_REFERENCE_COMPARISON_v1/top10_comparison.csv') if x['class_id']=='C0002792')
  self.assertEqual(x['source_terms'],'');self.assertEqual(x['reference_absence_is_negative'],'False');self.assertEqual(x['human_review'],'PENDING')
 def test_each_shap_record_has_the_correct_model_and_key(self):
  locked=rows(Q/'tedizolid_B1_SHAP_v1/local_feature_SHAP.csv');keys={(x['class_id'],x['fold'],x['feature']) for x in locked};self.assertEqual(len(keys),300);self.assertTrue(all(x['drug_id']=='DB14569' and x['model']=='B1' for x in locked))
  sel=[x for x in locked if x['class_id']=='C0011991' and x['fold']=='1'];self.assertEqual(max(sel,key=lambda x:float(x['SHAP_logit']))['feature'],'chem__HBD');self.assertEqual(min(sel,key=lambda x:float(x['SHAP_logit']))['feature'],'chem__HBA')
 def test_all_graph_inputs_are_exact_copies(self):
  for wp,fn in [('WP06','protein_string_mapping.csv'),('WP07','ppi_edge_provenance.csv'),('WP07','typed_drug_protein_edges.csv'),('WP07','drug_nodes.csv'),('WP07','protein_nodes.csv')]:
   self.assertEqual((O/'graf_v1'/fn).read_bytes(),(R/'reports/qa'/wp/fn).read_bytes())
 def test_reported_roles_and_ppi_are_separate(self):
  rel=rows(O/'graf_v1/typed_drug_protein_edges.csv');self.assertEqual(len({(x['drug_id'],x['accession'],x['role']) for x in rel}),476);self.assertEqual(len({(x['drug_id'],x['accession']) for x in rel}),457)
  e=rows(O/'graf_v1/ppi_kenar_onemi.csv');self.assertEqual(len(e),184);self.assertTrue(all(int(x['string_guveni_QA'])>=700 for x in e))
 def test_evidence_inventory_provenance(self):
  for x in rows(O/'EMT2_EVIDENCE_INVENTORY.csv'):
   p=R/(x['cikti'] if x['ayrinti']=='ek' else x['yontem_ve_kanit']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
if __name__=='__main__':unittest.main()

