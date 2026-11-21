import sys,json,tempfile,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from wp02_drugbank import iter_records,identity_index,resolve,duplicate_primary_ids

def parse(body):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'fixture.xml';p.write_text('<drugbank xmlns="urn:test">'+body+'</drugbank>',encoding='utf-8')
        return list(iter_records(p,{}))

def drug(i='DB00001',extra=''):
    return f'<drug type="small molecule"><drugbank-id primary="true">{i}</drugbank-id><name>Example</name>{extra}</drug>'

class ParserTests(unittest.TestCase):
    def test_only_top_level_drug_and_direct_atc(self):
        nested='<drug-interactions>'+drug('DB99999','<atc-codes><atc-code code="J01AA01"/></atc-codes>')+'</drug-interactions>'
        r=parse(drug(extra=nested))
        self.assertEqual(len(r),1);self.assertFalse(r[0]['j01']);self.assertEqual(r[0]['id'],'DB00001')

    def test_secondary_id_is_not_primary(self):
        r=parse(drug(extra='<drugbank-id>DB00002</drugbank-id>'))
        self.assertEqual(r[0]['secondary_ids'],['DB00002'])
        self.assertEqual(resolve('DB00002',identity_index(r))['parents'],['DB00001'])

    def test_salt_parent_evidence_and_no_name_mapping(self):
        r=parse(drug(extra='<salts><salt><drugbank-id>DBSALT0001</drugbank-id><name>Example salt</name></salt></salts>'))
        ix=identity_index(r)
        self.assertEqual(resolve('DBSALT0001',ix)['parents'],['DB00001'])
        self.assertEqual(resolve('Example salt',ix)['status'],'unresolved')

    def test_ambiguous_salt_not_arbitrarily_merged(self):
        salt='<salts><salt><drugbank-id>DBSALT1</drugbank-id></salt></salts>'
        r=parse(drug(extra=salt)+drug('DB00002',salt))
        self.assertEqual(resolve('DBSALT1',identity_index(r))['status'],'ambiguous')

    def test_j01_filter_and_multi_atc(self):
        r=parse(drug(extra='<atc-codes><atc-code code="J01AA01"/><atc-code code="D01AA01"/></atc-codes>'))
        self.assertTrue(r[0]['j01']);self.assertEqual(len(r[0]['atc']),2)
        self.assertFalse(parse(drug(extra='<atc-codes><atc-code code="J01BAD"/></atc-codes>'))[0]['j01'])

    def test_amino_acid_tag_and_conflicting_ids(self):
        target='<targets><target><id>T1</id><polypeptide id="P1"><amino-acid-sequence>&gt;header\nACDE</amino-acid-sequence><external-identifiers><external-identifier><resource>UniProtKB</resource><identifier>P2</identifier></external-identifier></external-identifiers></polypeptide></target></targets>'
        t=parse(drug(extra=target))[0]['targets'][0]
        self.assertTrue(t['aa_sequence_present']);self.assertFalse(t['old_sequence_tag_present'])
        self.assertEqual(t['id_status'],'conflict');self.assertEqual(t['uniprot_id'],'')

    def test_multiple_primary_not_silently_selected(self):
        r=parse(drug(extra='<drugbank-id primary="true">DB00002</drugbank-id>'))[0]
        self.assertEqual(r['primary_count'],2);self.assertEqual(r['id'],'')

    def test_salt_primary_attribute_does_not_override_parent(self):
        r=parse(drug(extra='<salts><salt><drugbank-id primary="true">DBSALT1</drugbank-id></salt></salts>'))
        self.assertEqual(r[0]['id'],'DB00001');self.assertEqual(r[0]['primary_count'],1)

    def test_duplicate_records_reported(self):
        r=parse(drug()+drug())
        self.assertEqual(duplicate_primary_ids(r),{'DB00001':2})

class SavedDataTests(unittest.TestCase):
    def test_full_parse_integrity_and_unique_ids(self):
        base=ROOT/'reports/qa/WP02'
        s=json.loads((base/'summary.json').read_text(encoding='utf-8'))
        m=json.loads((base/'parse_manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(m['parse_complete']);self.assertTrue(m['metadata_unchanged'])
        self.assertEqual(m['bytes_read'],m['size_bytes'])
        self.assertEqual(s['invalid_primary_records'],0);self.assertEqual(s['duplicate_primary_ids'],{})

    def test_mapping_and_cohort_reconcile(self):
        base=ROOT/'reports/qa/WP02'
        rows=json.loads((base/'drug_registry.json').read_text(encoding='utf-8'))
        s=json.loads((base/'summary.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(r['j01'] for r in rows),s['j01'])
        m=json.loads((base/'old209_mapping.json').read_text(encoding='utf-8'))
        self.assertEqual(len(m),209)
        self.assertEqual(len({r['parent_id'] for r in m if r['status']=='resolved'}),s['old209_unique_parents'])
        for r in m:
            if r['status']=='resolved':self.assertEqual(len(r['parents']),1)

    def test_previous_outputs_unchanged(self):
        prior=json.loads((ROOT/'reports/qa/WP02/prior_outputs_hashes.json').read_text())
        for path,sha in prior.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha,path)

    def test_combination_partition_and_bridge(self):
        base=ROOT/'reports/qa/WP02'
        s=json.loads((base/'summary.json').read_text(encoding='utf-8'))
        self.assertEqual(s['j01'],s['j01_noncombination']+s['j01_combination_only'])
        self.assertEqual(s['old38_j01'],27);self.assertEqual(s['old38_noncombination'],26)
        b=json.loads((base/'bridge_qc.json').read_text(encoding='utf-8'))
        self.assertEqual(len(b['rows']),s['j01']);self.assertEqual(b['missing_bridge'],0)
        self.assertEqual(b['conflicting_nonempty_cid'],[])

    def test_executed_notebook_has_real_outputs(self):
        import nbformat
        nb=nbformat.read(ROOT/'notebooks/WP02_drugbank_exploration.ipynb',as_version=4);nbformat.validate(nb)
        cells=[c for c in nb.cells if c.cell_type=='code']
        self.assertTrue(all(c.execution_count and c.outputs for c in cells))
        outputs=[o for c in cells for o in c.outputs]
        self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertGreaterEqual(sum('image/png' in o.get('data',{}) for o in outputs),7)

if __name__=='__main__':unittest.main(verbosity=2)
