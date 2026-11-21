import unittest,json,sys,hashlib,csv
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp03_sider import decode_stitch,encode_stitch,resolve_candidate,SIDER
QA=ROOT/'reports/qa/WP03'

class IdentityTests(unittest.TestCase):
    def test_flat_and_stereo_have_distinct_semantics(self):
        self.assertEqual(decode_stitch('CID100000085','flat'),'85')
        self.assertEqual(decode_stitch('CID000010917','stereo'),'10917')
        self.assertNotEqual(decode_stitch('CID100000085','flat'),'100000085')

    def test_wrong_type_and_invalid_format_rejected(self):
        for value,kind in [('CID100000085','stereo'),('CID000010917','flat'),('10917','stereo'),('CID000000000','stereo')]:
            with self.assertRaises(ValueError):decode_stitch(value,kind)

    def test_roundtrip_and_large_modern_cid(self):
        for cid in ['85','10917','123456789']:
            for kind in ['flat','stereo']:self.assertEqual(decode_stitch(encode_stitch(cid,kind),kind),cid)

    def test_exact_and_flat_only_not_equivalent(self):
        s={'CID000010917':{'CID100000085'}};f={'CID100000085':{'CID000010917'}}
        self.assertEqual(resolve_candidate('10917',['10917'],s,f,{'10917':['DB1']})[0],'exact_stereo_cid')
        self.assertEqual(resolve_candidate('85',['85'],s,f,{'85':['DB2']})[0],'ambiguous_flat_only')

    def test_shared_cid_xml_conflict_and_missing_cid(self):
        self.assertEqual(resolve_candidate('12',['12'],{}, {},{'12':['A','B']})[0],'ambiguous_shared_cid')
        self.assertEqual(resolve_candidate('12',['13'],{}, {},{'12':['A']})[0],'ambiguous_xml_bridge_conflict')
        self.assertEqual(resolve_candidate('',[],{}, {},{})[0],'unmatched_no_cid')

    def test_sid_not_accepted_as_a_stitch_token(self):
        with self.assertRaises(ValueError):decode_stitch('SID46508487','stereo')

class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=pd.read_csv(QA/'drug_mapping.csv',keep_default_na=False)
        cls.u=pd.read_csv(QA/'drug_pt_positives.csv',keep_default_na=False)
        cls.s=json.loads((QA/'coverage_summary.json').read_text(encoding='utf-8'))

    def test_partition_and_coverage(self):
        c=self.s['conservative']
        self.assertEqual(c['candidates'],233)
        self.assertEqual(sum(c['status_counts'].values()),233)
        self.assertEqual(c['with_pt'],62)
        self.assertEqual(c['retained_old38']+c['new_vs_old38'],62)
        self.assertEqual(c['all_three'],35)

    def test_unique_valid_positive_keys_and_trace(self):
        self.assertFalse(self.u.duplicated(['id','meddra_cui']).any())
        self.assertTrue(self.u.meddra_cui.str.fullmatch(r'C\d{7}').all())
        accepted=set(self.m[self.m.status.eq('exact_stereo_cid')].id)
        self.assertTrue(set(self.u.id)<=accepted)
        e=pd.read_csv(QA/'pt_evidence.csv')
        self.assertTrue((e.source_line>=1).all())
        self.assertEqual(set(zip(e.id,e.meddra_cui)),set(zip(self.u.id,self.u.meddra_cui)))

    def test_telavancin_not_in_exact_positives(self):
        r=self.m[self.m.id.eq('DB06402')].iloc[0]
        self.assertEqual(r.status,'ambiguous_flat_only')
        self.assertNotIn('DB06402',set(self.u.id))

    def test_every_evidence_line_matches_the_raw_pt_record(self):
        e=pd.read_csv(QA/'pt_evidence.csv',dtype=str,keep_default_na=False)
        expected={int(r.source_line):(r.flat_id,r.stereo_id,r.label_cui,'PT',r.meddra_cui,r.term) for r in e.itertuples()}
        found=set()
        with SIDER.open(encoding='utf-8',newline='') as f:
            for line,row in enumerate(csv.reader(f,delimiter='\t'),1):
                if line in expected:
                    self.assertEqual(tuple(row),expected[line]);found.add(line)
        self.assertEqual(found,set(expected))

    def test_old_reference_reproduced_from_raw(self):
        r=json.loads((QA/'legacy_comparison.json').read_text(encoding='utf-8'))
        self.assertEqual(r['reference_all_legacy_keys_in_raw_sider'],865)
        self.assertEqual(r['old38_unique_pairs'],590)
        self.assertEqual(r['rebuilt_old38_unique_categories_from_raw'],590)
        self.assertEqual(r['rebuilt_old38_unique_pt_from_raw'],605)

    def test_raw_integrity_and_old_outputs(self):
        manifest=json.loads((QA/'source_manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(manifest['metadata_unchanged'])
        prior=json.loads((QA/'prior_outputs_hashes.json').read_text())
        for p,h in prior.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)

    def test_notebook_executed_and_labels_remain_audits(self):
        import nbformat
        nb=nbformat.read(ROOT/'notebooks/WP03_sider_exploration.ipynb',as_version=4);nbformat.validate(nb)
        c=[x for x in nb.cells if x.cell_type=='code']
        self.assertTrue(all(x.execution_count and x.outputs for x in c))
        outputs=[o for x in c for o in x.outputs]
        self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertGreaterEqual(sum('image/png' in o.get('data',{}) for o in outputs),7)
        self.assertTrue(any('Nihai 30 kategori' in x.source for x in nb.cells))

if __name__=='__main__':unittest.main(verbosity=2)
