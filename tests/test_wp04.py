import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
import xml.etree.ElementTree as ET
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp04_chemistry import parse_smiles,identity,descriptors,compare_keys,FEATURES,Chem,rdMolDescriptors,atom_bond_tables
from wp04_extract import chemical_record,extract
from wp04_pubchem import PubChemClient
QA=ROOT/'reports/qa/WP04'


class ChemistryUnitTests(unittest.TestCase):
    def test_missing_and_invalid_smiles_not_filled(self):
        for s in ['',None,'C(C','CN(C)(C)C']:
            m,status=parse_smiles(s);self.assertIsNone(m);self.assertNotEqual(status,'valid')
            self.assertTrue(all(x is None for x in descriptors(m).values()))

    def test_known_small_molecule_descriptors_and_units(self):
        m,status=parse_smiles('CCO');d=descriptors(m)
        self.assertEqual(status,'valid');self.assertAlmostEqual(d['MW'],46.069,places=3)
        self.assertEqual(d['HBD'],1);self.assertEqual(d['HBA'],1);self.assertAlmostEqual(d['TPSA'],20.23,places=2)

    def test_atom_order_does_not_change_identity_or_features(self):
        a,_=parse_smiles('CCO');b,_=parse_smiles('OCC')
        self.assertEqual(identity(a)['rdkit_inchikey'],identity(b)['rdkit_inchikey'])
        for k in FEATURES:self.assertAlmostEqual(descriptors(a)[k],descriptors(b)[k],places=8)

    def test_enantiomers_distinct_full_keys_same_connectivity(self):
        a,_=parse_smiles('C[C@H](O)C(=O)O');b,_=parse_smiles('C[C@@H](O)C(=O)O')
        ak=identity(a)['rdkit_inchikey'];bk=identity(b)['rdkit_inchikey']
        self.assertNotEqual(ak,bk);self.assertEqual(compare_keys(ak,bk),'same_connectivity_other_layers_differ')

    def test_multicomponent_and_metal_not_removed(self):
        m,_=parse_smiles('[Na+].CC(=O)[O-]');before=(m.GetNumAtoms(),m.GetNumBonds())
        info=identity(m);self.assertEqual(info['components'],2);self.assertEqual(info['metal_atoms'],'Na')
        self.assertIn('.',info['rdkit_isomeric_smiles']);descriptors(m)
        self.assertEqual(before,(m.GetNumAtoms(),m.GetNumBonds()))

    def test_explicit_tpsa_s_p_definition(self):
        m,_=parse_smiles('OC(=O)P(=O)(O)O')
        self.assertAlmostEqual(descriptors(m)['TPSA'],94.83,places=2)
        self.assertGreater(rdMolDescriptors.CalcTPSA(m,includeSandP=True),descriptors(m)['TPSA'])

    def test_aromatic_atom_and_bond_tables_are_complete(self):
        m,_=parse_smiles('c1ccccc1');a,b=atom_bond_tables(m)
        self.assertEqual(len(a),6);self.assertEqual(len(b),6)
        self.assertTrue(all(x['aromatic'] for x in a));self.assertTrue(all(x['bond_type']=='AROMATIC' for x in b))

    def test_xml_nested_ids_and_property_sources_preserved(self):
        xml='''<drug xmlns="http://www.drugbank.ca" type="small molecule"><drugbank-id primary="true">DB00001</drugbank-id><name>A</name><salts><salt><drugbank-id primary="true">DBSALT01</drugbank-id></salt></salts><calculated-properties><property><kind>SMILES</kind><value>CCO</value><source>A</source></property><property><kind>logP</kind><value>1</value><source>A</source></property><property><kind>logP</kind><value>2</value><source>B</source></property></calculated-properties></drug>'''
        r=chemical_record(ET.fromstring(xml),1)
        self.assertEqual(r['id'],'DB00001');self.assertEqual(r['salt_links'][0]['id'],'DBSALT01')
        self.assertEqual(len([x for x in r['properties'] if x['kind']=='logP']),2)

    def test_streaming_only_top_level_and_stops_after_selected(self):
        xml='''<drugbank xmlns="http://www.drugbank.ca"><drug><drugbank-id primary="true">DB00001</drugbank-id><drug-interactions><drug><drugbank-id>DB99999</drugbank-id></drug></drug-interactions></drug><drug><drugbank-id primary="true">DB00002</drugbank-id></drug><drug><drugbank-id primary="true">DB00003</drugbank-id></drug></drugbank>'''
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'example.xml';p.write_text(xml,encoding='utf-8')
            rows,meta=extract(p,{'DB00002'})
        self.assertEqual([r['id'] for r in rows],['DB00002']);self.assertEqual(meta['records_scanned'],2)
        self.assertTrue(meta['stopped_early']);self.assertTrue(meta['metadata_unchanged'])


class PubChemClientTests(unittest.TestCase):
    def test_no_sid_name_or_out_of_scope_cid(self):
        c=PubChemClient('unused',{'12560'})
        for ids in [['SID12560'],['erythromycin'],['999'],['12560','12560']]:
            with self.assertRaises(ValueError):c.url(ids)

    def test_network_disabled_by_default(self):
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            c=PubChemClient(tmp,{'12560'})
            with self.assertRaises(RuntimeError):c.fetch(['12560'],'local missing (synthetic test)')
            self.assertEqual(c.requests_made,0)

    def test_cache_and_returned_cid_validation(self):
        session=Mock();response=Mock(status_code=200,content=b'synthetic payload')
        response.json.return_value={'PropertyTable':{'Properties':[{'CID':12560,'SMILES':'CCO'}]}}
        response.raise_for_status.return_value=None;session.get.return_value=response
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            c=PubChemClient(tmp,{'12560'},True,1,session)
            first=c.fetch(['12560'],'synthetic unit response; not real compound evidence')
            second=c.fetch(['12560'],'same unit cache');self.assertEqual(first,second)
            self.assertEqual(session.get.call_count,1);self.assertEqual(c.requests_made,1)
            with self.assertRaises(ValueError):c.validate({'PropertyTable':{'Properties':[{'CID':1}]}},['12560'])

    def test_failed_response_is_logged_not_cached_success(self):
        session=Mock();session.get.side_effect=RuntimeError('synthetic offline')
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            c=PubChemClient(tmp,{'12560'},True,1,session)
            with self.assertRaises(RuntimeError):c.fetch(['12560'],'synthetic test')
            self.assertFalse(list(Path(tmp).glob('*.json')))
            self.assertIn('failed',(Path(tmp)/'request_log.jsonl').read_text())
            with self.assertRaises(RuntimeError):c.fetch(['12560'],'budget should block retry')


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=pd.read_csv(QA/'structure_validation.csv',keep_default_na=False)
        cls.raw=pd.read_csv(QA/'chemical_features_raw.csv');cls.clean=pd.read_csv(QA/'chemical_features_clean.csv')

    def test_62_unique_source_identities_and_no_conflicts(self):
        self.assertEqual(len(self.q),62);self.assertEqual(self.q.id.nunique(),62)
        self.assertTrue(self.q.cid_verified.all());self.assertTrue(self.q.identity_verified_local.all())
        self.assertTrue(self.q.smiles_key_relation.eq('full_inchikey_match').all())

    def test_feature_schema_excludes_all_label_qa_columns(self):
        expected=['id',*FEATURES]
        self.assertEqual(self.raw.columns.tolist(),expected);self.assertEqual(self.clean.columns.tolist(),expected)
        self.assertEqual(self.raw.id.nunique(),62);self.assertTrue(self.raw[list(FEATURES)].notna().all().all())

    def test_strict_qc_holds_review_rows_not_imputation(self):
        joined=self.clean.merge(self.q[['id','strict_qc_pass']],on='id',validate='one_to_one')
        self.assertTrue(joined.loc[~joined.strict_qc_pass,list(FEATURES)].isna().all().all())
        self.assertTrue(joined.loc[joined.strict_qc_pass,list(FEATURES)].notna().all().all())
        self.assertEqual(joined.strict_qc_pass.sum(),54)

    def test_recovery_21_raw_18_strict_and_legacy_cid(self):
        r=pd.read_csv(QA/'coverage_and_recovery.csv');old=pd.read_csv(QA/'legacy_feature_comparison.csv')
        self.assertEqual((~r.old_chemistry_available).sum(),21);self.assertEqual(r.newly_computed_raw.sum(),21)
        self.assertEqual(r.recovered_strict.sum(),18);self.assertTrue(old[old.old_value.notna()].cid_agrees.all())

    def test_gentamicin_intact_and_methenamine_algorithm_flag(self):
        q=self.q.set_index('id');self.assertEqual(q.loc['DB00798','components'],3)
        self.assertEqual(q.loc['DB00798','formula'],'C60H123N15O21')
        self.assertEqual(q.loc['DB06799','legacy_chiral_unassigned'],0)
        self.assertEqual(q.loc['DB06799','chiral_unassigned'],4)

    def test_source_and_prior_outputs_integrity(self):
        meta=json.loads((QA/'xml_extract_manifest.json').read_text(encoding='utf-8'))
        stat=Path(meta['source']).stat()
        self.assertEqual(stat.st_size,meta['size_bytes']);self.assertEqual(stat.st_mtime_ns,meta['mtime_ns'])
        prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
        for path,h in prior.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h,path)

    def test_notebook_executed_real_tables_and_full_molecule_images(self):
        import nbformat
        nb=nbformat.read(ROOT/'notebooks/WP04_molecular_exploration.ipynb',as_version=4);nbformat.validate(nb)
        code=[c for c in nb.cells if c.cell_type=='code'];self.assertGreaterEqual(len(code),12)
        self.assertTrue(all(c.execution_count and c.outputs for c in code))
        outputs=[o for c in code for o in c.outputs];self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertGreaterEqual(sum('image/png' in o.get('data',{}) for o in outputs),10)
        for drug in ['DB01060','DB00537','DB00207']:self.assertTrue((ROOT/f'reports/figures/WP04/{drug}_2D.png').exists())


if __name__=='__main__':unittest.main(verbosity=2)
