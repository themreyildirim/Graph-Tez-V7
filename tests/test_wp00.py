"""İzolasyon, şema, örnekleme ve protein parse QC testleri; model testi değildir."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit', ROOT / 'scripts/wp00_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class AuditUnitTests(unittest.TestCase):
    def test_excluded_folders_are_never_entered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ['CARD', 'MIMIC-IV', 'UniProt Dataset', 'string-db/Staphylococcus aureus']:
                (root / name).mkdir(parents=True)
                (root / name / 'full database.xml').write_text('DO NOT READ')
            original = Path.iterdir
            entered = []
            def guarded(path):
                entered.append(path)
                self.assertIn(path, audit.allowed_directories(root))
                return original(path)
            with patch.object(Path, 'iterdir', guarded):
                rows = audit.inventory(root)
            self.assertTrue(any(r['name']=='CARD' and r['status']=='excluded' for r in rows))
            self.assertFalse(any(r['name']=='full database.xml' and r['status']=='exists' for r in rows))

    def test_xml_only_top_level_drug_and_amino_acid_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'full database.xml'
            drug = '''<drug><drugbank-id primary="true">DB1</drugbank-id><name>outer</name>
            <drug-interactions><drug><name>nested</name></drug></drug-interactions>
            <targets><target><polypeptide id="P1"><amino-acid-sequence format="FASTA">&gt;protein
            ACDE</amino-acid-sequence><gene-sequence>ACGT</gene-sequence></polypeptide></target></targets></drug>'''
            path.write_text('<drugbank xmlns="urn:test" version="test">'+drug*4+'</drugbank>', encoding='utf-8')
            p = audit.sample_xml(path)
            self.assertEqual(p['sample_size'], 3)
            self.assertTrue(all(r['name']=='outer' for r in p['examples']))
            seq = p['examples'][0]['target_polypeptides'][0]['sequences']
            self.assertEqual(len(seq), 1)
            self.assertEqual(seq[0]['tag'], 'amino-acid-sequence')
            self.assertEqual(seq[0]['sequence_length'], 4)

    def test_fasta_header_not_counted_as_amino_acids(self):
        self.assertEqual(audit.parse_sequence('>lcl|BSEQ|Metadata ACDE\nACDE\nFGHIKLMNPQRSTVWY\n'), 'ACDEFGHIKLMNPQRSTVWY')

    def test_collapsed_header_rejected(self):
        with self.assertRaisesRegex(ValueError, 'header_boundary_lost'):
            audit.parse_sequence('>lcl|BSEQ|DescriptionACDE')

    def test_invalid_and_ambiguous_sequence_rejected(self):
        for seq in ['', 'ACDEX', 'ACDEU', 'ACDEO', 'ACDEB', 'ACDEZ', 'ACDE1', 'ACDE*', 'ACDE metadata']:
            with self.subTest(seq=seq), self.assertRaises(ValueError):
                audit.parse_sequence(seq)

    def test_sider_headerless_missingness_duplicates_and_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'meddra_all_se.tsv'
            row = 'CID100000085\tCID000010917\tC0000729\t\t\tAbdominal cramps\n'
            path.write_text(row*1002, encoding='utf-8')
            p = audit.sample_table(path)
            self.assertEqual(p['sample_size'], 1000)
            self.assertFalse(p['complete_file_read'])
            self.assertEqual(p['duplicate_full_rows_excess'], 999)
            self.assertEqual(p['columns'][3]['missing_count'], 1000)
            self.assertEqual(p['details']['stitch_pattern_invalid_rows'], 0)

    def test_malformed_rows_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'drug links.csv'
            path.write_text('DrugBank ID,PubChem Compound ID\nDB1,12\nDB2\n', encoding='utf-8')
            p = audit.sample_table(path)
            self.assertEqual(p['malformed_row_numbers_in_sample'], [2])

class SavedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT/'reports/qa/profiles.json').read_text(encoding='utf-8'))
        with (ROOT/'reports/qa/data_inventory.csv').open(encoding='utf-8-sig', newline='') as f:
            cls.rows = list(csv.DictReader(f))

    def test_manifest_alias_and_allowed_content(self):
        self.assertEqual((ROOT/'reports/qa/data_inventory.csv').read_bytes(), (ROOT/'reports/qa/source_inventory.csv').read_bytes())
        self.assertTrue(set(self.profiles).issubset(audit.ALLOW))
        for r in self.rows:
            if r['source']=='out_of_scope':
                self.assertEqual(r['inspected'], 'False')
                self.assertEqual(r['size_bytes'], '')

    def test_real_sample_limits_and_schemas(self):
        xml = self.profiles['full database.xml']
        self.assertEqual(xml['sample_size'], 3)
        self.assertFalse(xml['whole_file_validated'])
        self.assertLess(xml['bytes_read_including_parser_buffer'], 10_000_000)
        for name,p in self.profiles.items():
            if p['kind']=='table':
                self.assertLessEqual(p['sample_size'], 1000)
                self.assertFalse(p['malformed_row_numbers_in_sample'])
                expected = audit.SIDER_COLUMNS if name=='meddra_all_se.tsv' else ['protein1','protein2','combined_score'] if '.links.' in name else ['#string_protein_id','alias','source']
                self.assertEqual([c['name'] for c in p['columns']], expected)

    def test_source_metadata_unchanged(self):
        record = json.loads((ROOT/'reports/qa/read_integrity.json').read_text(encoding='utf-8'))
        self.assertEqual(len(record['checks']), len(self.profiles))
        self.assertTrue(all(c['metadata_unchanged'] for c in record['checks']))
        self.assertEqual(record['network_calls'], 0)

    def test_real_prefix_and_taxon_checks(self):
        self.assertEqual(self.profiles['meddra_all_se.tsv']['details']['stitch_pattern_invalid_rows'], 0)
        for tax in ['9606', '511145']:
            self.assertEqual(self.profiles[f'{tax}.protein.links.v12.0.txt']['details']['taxon_prefix_invalid_rows'], 0)

class DriveArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=json.loads((ROOT/'reports/qa/drive_profiles.json').read_text(encoding='utf-8'))
        cls.findings=json.loads((ROOT/'reports/qa/drive_findings.json').read_text(encoding='utf-8'))

    def test_complete_text_lengths_and_metadata(self):
        self.assertEqual(len(self.profiles),7)
        self.assertTrue(all(p['size_matches'] for p in self.profiles.values()))
        integrity=json.loads((ROOT/'reports/qa/drive_integrity.json').read_text(encoding='utf-8'))
        self.assertTrue(all(c['metadata_unchanged'] for c in integrity['checks']))
        self.assertFalse(integrity['raw_csv_saved_to_local_disk'])

    def test_legacy_shapes_match_source_summary(self):
        expected={'ilac_feature_v5_atc.csv':(56,33),'protein_feature_v6.csv':(70,54),
                  'protein_dizileri_v6.csv':(70,4),'ilac_protein_eslesmesi_v6.csv':(153,5)}
        for name,shape in expected.items():
            p=self.profiles[name]
            self.assertEqual((p['rows'],p['column_count']),shape)

    def test_unique_pairs_and_unknown_arithmetic(self):
        p=self.findings['adr']
        self.assertEqual(p['intersection_unique_pairs'],590)
        self.assertEqual(p['intersection_rows']-p['intersection_unique_pairs'],15)
        self.assertEqual(p['possible_pairs'],38*30)
        self.assertEqual(p['unknown_pairs'],p['possible_pairs']-p['intersection_unique_pairs'])
        self.assertEqual(p['unique_pairs'],844)

    def test_source_trace_all_legacy_records(self):
        t=json.loads((ROOT/'reports/qa/source_trace.json').read_text(encoding='utf-8'))
        self.assertEqual(t['query_rows'],865)
        self.assertEqual(t['matched_unique_queries'],t['unique_queries'])
        self.assertEqual(t['unmatched_queries'],[])
        self.assertTrue(t['metadata_unchanged'])

    def test_id_bridge_and_forbidden_feature_evidence(self):
        f=self.findings
        self.assertEqual(f['bridge']['feature_cid_mismatch'],[])
        self.assertEqual(len(f['bridge']['candidate_db_missing']),f['candidates']['dbsalt'])
        self.assertEqual(f['protein']['prefix_rule_matches'],70)
        self.assertEqual(f['protein']['collapsed_header_rows'],70)
        self.assertEqual(len(f['atc']['all_zero']),12)

if __name__ == '__main__':
    unittest.main(verbosity=2)
