from pathlib import Path
import sys,json,hashlib,tempfile,unittest
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp05_proteins import parse_sequence,resolve_accession,features,validate_groups,organism_class,AA,GROUPS
from wp05_extract import extract_record,stream_extract
from wp05_analyze import classify_without_polypeptide
QA=ROOT/'reports/qa/WP05'


class SequenceTests(unittest.TestCase):
    def test_fasta_header_removed_before_aac(self):
        p=parse_sequence('>lcl|BSEQ1|AminoAcidSequence DESCRIPTION\nac d\nEF\n')
        self.assertEqual(p['sequence'],'ACDEF');self.assertEqual(p['length'],5);self.assertTrue(p['header_removed'])
        self.assertEqual(features(p['sequence'])['AAC_A'],.2)

    def test_header_boundary_missing_not_guessed(self):
        p=parse_sequence('>lcl|BSEQ1|ProteinNameMAAACDE')
        self.assertEqual(p['status'],'fasta_missing_sequence_boundary');self.assertEqual(p['sequence'],'')

    def test_multiple_fasta_records_and_embedded_header_rejected(self):
        for raw in ['>a\nACD\n>b\nEFG','ACD\n>b\nEFG']:
            self.assertNotEqual(parse_sequence(raw)['status'],'valid')

    def test_unknowns_numbers_html_and_unicode_not_silently_deleted(self):
        for raw in ['ACXDE','A1CDE','AC<BR>DE','ACD*','ABZJOU','AßC']:
            self.assertEqual(parse_sequence(raw)['status'],'invalid_residues_or_markup')
            self.assertEqual(parse_sequence(raw)['sequence'],'')

    def test_missing_and_single_residue_semantics(self):
        self.assertEqual(parse_sequence(' \n')['status'],'missing')
        with self.assertRaises(ValueError):features('')
        with self.assertRaises(ValueError):features('AX')
        f=features('A');self.assertTrue(all(v is None for k,v in f.items() if k.startswith('DC_')))

    def test_groups_cover_all20_disjoint_and_dc_denominator(self):
        validate_groups();self.assertEqual(set(''.join(GROUPS.values())),set(AA))
        self.assertEqual(len(''.join(GROUPS.values())),20)
        with self.assertRaises(ValueError):validate_groups({'a':'AC','b':'AC'})
        f=features('CFGA');self.assertAlmostEqual(sum(v for k,v in f.items() if k.startswith('AAC_')),1)
        self.assertAlmostEqual(sum(v for k,v in f.items() if k.startswith('DC_')),1)
        self.assertAlmostEqual(f['DC_polar_uncharged__aromatic'],1/3)

    def test_known_mass_aromaticity_and_reference_pi_charge(self):
        f=features('AA');self.assertAlmostEqual(f['molecular_weight_Da'],160.1711,places=3)
        self.assertEqual(features('FWYA')['aromaticity_fraction'],.75)
        f=features('INGAR');self.assertAlmostEqual(f['isoelectric_point'],9.75,places=2)
        self.assertAlmostEqual(f['net_charge_pH7'],.76,places=2)

    def test_accession_conflict_and_malformed_id(self):
        self.assertEqual(resolve_accession('P02768',['P02768'])[0],'P02768')
        self.assertEqual(resolve_accession('P02768',['Q12809'])[1],'conflicting_accessions')
        self.assertEqual(resolve_accession('BSEQ123',[])[1],'invalid_accession_format')
        self.assertEqual(resolve_accession('',[])[1],'missing_accession')

    def test_nonhuman_not_automatically_bacteria(self):
        self.assertEqual(organism_class('Yeast'),'fungus');self.assertEqual(organism_class('Mouse'),'other_eukaryote')
        self.assertEqual(organism_class('Plasmodium falciparum'),'other_eukaryote')
        self.assertEqual(organism_class('uncurated species'),'other_or_unresolved')
        self.assertEqual(organism_class('Escherichia coli'),'bacteria')

    def test_peptidoglycan_enzyme_not_nonprotein_cell_wall(self):
        self.assertEqual(classify_without_polypeptide('Peptidoglycan transpeptidase'),'protein_named_missing_polypeptide')
        self.assertEqual(classify_without_polypeptide('30S ribosomal protein'),'protein_named_missing_polypeptide')
        self.assertEqual(classify_without_polypeptide('23S ribosomal RNA'),'nonprotein_rRNA')


class XmlTests(unittest.TestCase):
    def test_four_roles_correct_sequence_path_and_source_ids(self):
        xml='''<drug xmlns="http://www.drugbank.ca"><drugbank-id primary="true">DB00001</drugbank-id><salts><salt><drugbank-id primary="true">DBSALT1</drugbank-id></salt></salts><targets><target><id>RNA1</id><name>23S ribosomal RNA</name></target></targets><enzymes><enzyme><id>BE1</id><polypeptide id="P02768" source="Swiss-Prot"><organism ncbi-taxonomy-id="9606">Humans</organism><amino-acid-sequence>&gt;test\nACDE</amino-acid-sequence></polypeptide></enzyme></enzymes><transporters><transporter><id>TR1</id></transporter></transporters><carriers><carrier><id>CA1</id></carrier></carriers></drug>'''
        r=extract_record(ET.fromstring(xml),1);self.assertEqual(r['id'],'DB00001')
        self.assertEqual({x['role'] for x in r['relations']},{'target','enzyme','transporter','carrier'})
        enzyme=next(x for x in r['relations'] if x['role']=='enzyme');self.assertIn('ACDE',enzyme['raw_sequence'])
        self.assertFalse(enzyme['old_sequence_tag_present']);self.assertEqual(enzyme['organism_attributes']['ncbi-taxonomy-id'],'9606')

    def test_stream_nested_drug_not_independent_and_early_stop(self):
        xml='''<drugbank xmlns="http://www.drugbank.ca"><drug><drugbank-id primary="true">DB00001</drugbank-id><drug-interactions><drug><drugbank-id>DB99999</drugbank-id></drug></drug-interactions></drug><drug><drugbank-id primary="true">DB00002</drugbank-id></drug></drugbank>'''
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            p=Path(tmp)/'example.xml';p.write_text(xml,encoding='utf-8');rows,meta=stream_extract(p,{'DB00001'})
        self.assertEqual(len(rows),1);self.assertEqual(meta['records_scanned'],1);self.assertTrue(meta['metadata_unchanged'])


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=json.loads((QA/'coverage_summary.json').read_text(encoding='utf-8'))
        cls.seq=pd.read_csv(QA/'protein_sequences.csv');cls.f=pd.read_csv(QA/'protein_features.csv')
        cls.e=pd.read_csv(QA/'drug_protein_edges.csv');cls.c=pd.read_csv(QA/'drug_coverage.csv')

    def test_independent_62_55_60_141_coverage(self):
        self.assertEqual(len(self.c),62);self.assertEqual(self.c.id.nunique(),62)
        self.assertEqual(self.e[self.e.role.eq('target')].drug_id.nunique(),55)
        self.assertEqual(self.e.drug_id.nunique(),60);self.assertEqual(self.e.accession.nunique(),141)
        self.assertEqual(len(self.seq),141);self.assertEqual(len(self.f),141)

    def test_typed_edges_unique_and_sequences_all_match(self):
        self.assertFalse(self.e.duplicated(['drug_id','accession','role']).any())
        self.assertEqual(len(self.e),476)
        self.assertEqual(len(self.e[['drug_id','accession']].drop_duplicates()),457)
        for r in self.seq.itertuples():
            self.assertTrue(set(r.sequence)<=set(AA));self.assertEqual(len(r.sequence),r.length_aa)
            self.assertEqual(hashlib.sha256(r.sequence.encode()).hexdigest(),r.sequence_sha256)
        from Bio import SeqIO
        with (QA/'validated_proteins.fasta').open(encoding='utf-8') as stream:
            exported=SeqIO.to_dict(SeqIO.parse(stream,'fasta'))
        self.assertEqual(set(exported),set(self.seq.accession))
        for r in self.seq.itertuples():self.assertEqual(str(exported[r.accession].seq),r.sequence)

    def test_features_sums_finite_and_no_labels_quality_or_ids_as_values(self):
        allowed={'accession','length_aa','molecular_weight_Da','isoelectric_point','aromaticity_fraction','gravy_kyte_doolittle','net_charge_pH7'}
        allowed|={'AAC_'+a for a in AA}|{'group_'+g for g in GROUPS}|{f'DC_{a}__{b}' for a in GROUPS for b in GROUPS}
        self.assertEqual(set(self.f.columns),allowed);self.assertTrue(np.isfinite(self.f.drop(columns='accession')).all().all())
        self.assertTrue(np.allclose(self.f.filter(regex='^AAC_').sum(axis=1),1))
        self.assertTrue(np.allclose(self.f.filter(regex='^DC_').sum(axis=1),1))
        self.assertTrue(np.allclose(self.f.filter(regex='^group_').sum(axis=1),1))

    def test_missing_two_retained_and_seven_roles_not_targets(self):
        missing=set(self.c[self.c.feature_proteins.eq(0)].id);self.assertEqual(missing,{'DB00684','DB06799'})
        self.assertTrue(self.c.retained_in_cohort.all())
        seven=pd.read_csv(QA/'priority_seven.csv');self.assertEqual(len(seven),7);self.assertTrue(seven.target_proteins.eq(0).all())
        self.assertEqual(seven[seven.feature_proteins.gt(0)].shape[0],5)

    def test_wp02_targets_match_and_wp04_all_eight_retained(self):
        self.assertTrue(json.loads((QA/'wp02_target_consistency.json').read_text())['all_match'])
        q=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv');held=set(q[~q.strict_qc_pass].id)
        self.assertEqual(len(held),8);self.assertTrue(held<=set(self.c.id))

    def test_organism_definition_29_groups_28_taxids(self):
        org=pd.read_csv(QA/'organism_summary.csv',keep_default_na=False)
        self.assertEqual(len(org),29);self.assertEqual(org[org.taxid.astype(str).ne('')].taxid.nunique(),28)
        self.assertEqual(self.s['organism_groups'],{'bacteria':75,'human':63,'fungus':1,'other_eukaryote':2})

    def test_raw_metadata_and_226_prior_files_unchanged(self):
        meta=json.loads((QA/'xml_extract_manifest.json').read_text(encoding='utf-8'));stat=Path(meta['source']).stat()
        self.assertEqual(stat.st_size,meta['size_bytes']);self.assertEqual(stat.st_mtime_ns,meta['mtime_ns'])
        prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
        for p,h in prior.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)

    def test_notebook_executed_and_graph_outputs_present(self):
        import nbformat
        nb=nbformat.read(ROOT/'notebooks/WP05_protein_exploration.ipynb',as_version=4);nbformat.validate(nb)
        cells=[c for c in nb.cells if c.cell_type=='code'];self.assertGreaterEqual(len(cells),11)
        self.assertTrue(all(c.execution_count and c.outputs for c in cells))
        outputs=[o for c in cells for o in c.outputs];self.assertFalse(any(o.output_type=='error' for o in outputs))
        self.assertGreaterEqual(sum('image/png' in o.get('data',{}) for o in outputs),11)
        html=(ROOT/'reports/figures/WP05/drug_protein_interactive.html').read_text(encoding='utf-8')
        self.assertIn('Plotly.newPlot',html);self.assertNotIn('<script src=',html)


if __name__=='__main__':unittest.main(verbosity=2)
