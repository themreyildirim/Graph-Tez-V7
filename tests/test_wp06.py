from pathlib import Path
import json,hashlib,sys,tempfile,unittest
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wp06_mapping import classify_mapping,scan_aliases,source_path
from wp06_ppi import valid_link,EdgeStore,network_metrics,scan_links
QA=ROOT/'reports/qa/WP06'


def hit(acc='P02768',sid='9606.A',tax='9606',source='UniProt_AC'):
    return {'accession':acc,'string_id':sid,'network_taxid':tax,'alias_source':source}


class IdentityTests(unittest.TestCase):
    def test_exact_accession_and_taxon(self):
        r=classify_mapping({'accession':'P02768','taxid':'9606'},[hit()])
        self.assertEqual(r['status'],'exact_alias_exact_taxon');self.assertTrue(r['strict_taxon_match'])

    def test_multiple_STRING_candidates_held(self):
        r=classify_mapping({'accession':'P02768','taxid':'9606'},[hit(),hit(sid='9606.B')])
        self.assertEqual(r['status'],'ambiguous_multiple_STRING_ids');self.assertEqual(r['string_id'],'')

    def test_gene_name_alias_not_accepted(self):
        r=classify_mapping({'accession':'P02768','taxid':'9606'},[hit(source='UniProt_GN_Name')])
        self.assertEqual(r['status'],'unmatched_accession_alias')

    def test_K12_parent_scope_never_silently_strict(self):
        r=classify_mapping({'accession':'P0A6F5','taxid':'83333'},[hit('P0A6F5','511145.b0001','511145')])
        self.assertEqual(r['status'],'exact_alias_K12_parent_scope_review');self.assertTrue(r['alias_identity_unique']);self.assertFalse(r['strict_taxon_match'])

    def test_other_bacterial_species_not_Ecoli(self):
        r=classify_mapping({'accession':'P0A6F5','taxid':'1280'},[hit('P0A6F5','511145.b0001','511145')])
        self.assertEqual(r['status'],'out_of_scope_organism');self.assertFalse(r['alias_identity_unique'])

    def test_species_level_mapping_kept_as_review(self):
        r=classify_mapping({'accession':'P0A6F5','taxid':'562'},[hit('P0A6F5','511145.b0001','511145')])
        self.assertEqual(r['status'],'exact_alias_species_strain_review');self.assertFalse(r['strict_taxon_match'])

    def test_source_allowlist_rejects_other_taxon(self):
        with self.assertRaises(ValueError):source_path(Path('.'),'1280','links')
        with self.assertRaises(ValueError):source_path(Path('.'),'9606','info')

    def test_alias_stream_exact_token_not_substring(self):
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            p=Path(tmp)/'aliases.txt';p.write_text('#string_protein_id\talias\tsource\n9606.A\tP02768\tUniProt_AC\n9606.B\tP02768-2\tUniProt_AC\n',encoding='utf-8')
            rows,meta=scan_aliases(p,'9606',{'P02768'})
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['source_line'],2);self.assertTrue(meta['metadata_unchanged'])


class GraphTests(unittest.TestCase):
    def test_taxon_score_selfloop_validation(self):
        self.assertEqual(valid_link('9606.A','511145.B','800','9606'),'taxon_prefix_mismatch')
        self.assertEqual(valid_link('9606.A','9606.A','800','9606'),'self_loop')
        self.assertEqual(valid_link('9606.A','9606.B','1001','9606'),'score_out_of_range')
        self.assertEqual(valid_link('9606.A','9606.B','NaN','9606'),'noninteger_score')

    def test_undirected_reciprocal_and_same_direction_duplicate(self):
        s=EdgeStore();s.add('9606.B','9606.A',700,2);s.add('9606.A','9606.B',700,3);s.add('9606.A','9606.B',700,4)
        rows=s.rows('9606');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['source_rows'],3)
        self.assertTrue(rows[0]['reciprocal_pair_observed']);self.assertEqual(rows[0]['same_direction_duplicate_excess'],1)

    def test_threshold_inclusive_isolates_retained_weight_not_degree(self):
        row={'protein1':'9606.A','protein2':'9606.B','combined_score':700,'score_conflict':False}
        m,g=network_metrics({'9606.A','9606.B','9606.C'},[row],700)
        self.assertEqual(m['edges'],1);self.assertEqual(m['isolates'],1);self.assertEqual(m['components'],2)
        self.assertAlmostEqual(g.degree('9606.A',weight='weight'),.7)
        higher,_=network_metrics(set(g),[row],701);self.assertEqual(higher['edges'],0);self.assertEqual(higher['isolates'],3)

    def test_score_conflict_is_withheld(self):
        s=EdgeStore();s.add('9606.A','9606.B',700,2);s.add('9606.B','9606.A',800,3)
        rows=s.rows('9606');self.assertTrue(rows[0]['score_conflict'])
        m,_=network_metrics({'9606.A','9606.B'},rows,150);self.assertEqual(m['edges'],0)

    def test_cross_taxon_or_undeclared_nodes_cannot_enter_graph(self):
        row={'protein1':'9606.A','protein2':'511145.B','combined_score':800,'score_conflict':False}
        with self.assertRaises(ValueError):network_metrics({'9606.A','511145.B'},[row],700)
        with self.assertRaises(ValueError):network_metrics({'9606.A'},[row],700)

    def test_stream_filters_and_bounded_neighbor_selection(self):
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            p=Path(tmp)/'links.txt';p.write_text('protein1 protein2 combined_score\n9606.A 9606.B 700\n9606.B 9606.A 700\n9606.A 9606.A 999\n9606.A 511145.X 900\n9606.A 9606.C 900\n',encoding='utf-8')
            rows,neighbors,meta,hist=scan_links(p,'9606',{'9606.A','9606.B'})
        self.assertEqual(len(rows),1);self.assertEqual(neighbors['9606.A'],{'9606.C':900})
        self.assertEqual(meta['self_loop'],1);self.assertEqual(meta['taxon_prefix_mismatch'],1)


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=pd.read_csv(QA/'protein_string_mapping.csv',dtype={'network_taxid':str},keep_default_na=False)
        cls.e=pd.read_csv(QA/'ppi_induced_edges.csv',dtype={'network_taxid':str})
        cls.x=pd.read_csv(QA/'ppi_expanded_edges.csv',dtype={'network_taxid':str})
        cls.metrics=pd.read_csv(QA/'network_metrics.csv',dtype={'network_taxid':str})

    def test_mapping_partition_and_141_proteins(self):
        self.assertEqual(self.m.accession.nunique(),141);self.assertEqual(self.m.alias_identity_unique.sum(),86)
        self.assertEqual(self.m.strict_taxon_match.sum(),63);self.assertEqual(self.m.status.eq('exact_alias_K12_parent_scope_review').sum(),23)
        self.assertEqual(self.m.status.eq('unmatched_accession_alias').sum(),6);self.assertEqual(self.m.status.eq('out_of_scope_organism').sum(),49)

    def test_every_mapping_has_exact_UniProt_AC_alias_evidence(self):
        a=pd.read_csv(QA/'alias_evidence.csv',dtype={'network_taxid':str})
        for r in self.m[self.m.alias_identity_unique].itertuples():
            subset=a[a.accession.eq(r.accession)&a.string_id.eq(r.string_id)&a.network_taxid.eq(r.network_taxid)]
            self.assertTrue(subset.alias_source.str.split().apply(lambda x:'UniProt_AC' in x).any())

    def test_retained_edges_canonical_nonself_nonconflicting(self):
        for data in [self.e,self.x]:
            self.assertTrue((data.protein1<data.protein2).all());self.assertFalse(data.duplicated(['network_taxid','protein1','protein2']).any())
            self.assertFalse(data.score_conflict.any());self.assertTrue(data.same_direction_duplicate_excess.eq(0).all())
            self.assertTrue(data.combined_score.between(150,999).all())
            for r in data.itertuples():self.assertTrue(r.protein1.startswith(r.network_taxid+'.') and r.protein2.startswith(r.network_taxid+'.'))

    def test_induced_counts_and_700_metrics_independently(self):
        self.assertEqual(self.e.groupby('network_taxid').size().to_dict(),{'511145':130,'9606':1200})
        for tax,expected in [('9606',(184,12,14)),('511145',(68,2,4))]:
            seeds=set(self.m[self.m.network_taxid.eq(tax)&self.m.alias_identity_unique].string_id)
            metrics,_=network_metrics(seeds,self.e[self.e.network_taxid.eq(tax)].to_dict('records'),700)
            self.assertEqual((metrics['edges'],metrics['isolates'],metrics['components']),expected)

    def test_context_nodes_not_claimed_drugbank_targets_or_features(self):
        n=pd.read_csv(QA/'ppi_nodes.csv',keep_default_na=False);c=n[n.node_role.eq('STRING_context_only')]
        self.assertEqual(len(c),80);self.assertTrue(c.sequence_feature_available.eq(False).all())
        self.assertTrue(c.drugbank_target_verified.astype(str).eq('False').all());self.assertTrue(c.accessions.eq('').all())

    def test_62_drugs_wp04_eight_and_two_missing_protein_preserved(self):
        c=pd.read_csv(QA/'drug_ppi_mapping_coverage.csv');self.assertEqual(len(c),62);self.assertTrue(c.retained_in_62.all())
        for d in ['DB00684','DB06799']:self.assertEqual(c.set_index('drug_id').loc[d,'WP05_proteins'],0)
        held=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv');self.assertTrue(set(held[~held.strict_qc_pass].id)<=set(c.drug_id))

    def test_old_forward_static_audit_and_no_legacy_execution(self):
        a=json.loads((QA/'legacy_forward_audit.json').read_text(encoding='utf-8'))
        self.assertFalse(a['ppi_argument_present']);self.assertIn('dp_ei',a['forward_args'])
        self.assertEqual(a['protein_encoder_expression'],'h_prot = self.prot_enc(x_prot)')

    def test_raw_metadata_and_prior_outputs_unchanged(self):
        manifests=json.loads((QA/'aliases_manifest.json').read_text(encoding='utf-8'))+json.loads((QA/'links_manifest.json').read_text(encoding='utf-8'))
        for m in manifests:
            st=Path(m['file']).stat();self.assertEqual(st.st_size,m['size_bytes']);self.assertEqual(st.st_mtime_ns,m['mtime_ns'])
        prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
        for p,h in prior.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)

    def test_executed_notebook_and_offline_HTML_edge_hover(self):
        import nbformat
        nb=nbformat.read(ROOT/'notebooks/WP06_string_ppi_exploration.ipynb',as_version=4);nbformat.validate(nb)
        c=[x for x in nb.cells if x.cell_type=='code'];self.assertGreaterEqual(len(c),10)
        self.assertTrue(all(x.execution_count and x.outputs for x in c));o=[a for x in c for a in x.outputs]
        self.assertFalse(any(x.output_type=='error' for x in o));self.assertGreaterEqual(sum('image/png' in x.get('data',{}) for x in o),9)
        for tax in ['9606','511145']:
            h=(ROOT/f'reports/figures/WP06/{tax}_ppi_interactive.html').read_text(encoding='utf-8')
            self.assertIn('combined_score=',h);self.assertIn('Plotly.newPlot',h);self.assertNotIn('<script src=',h)


if __name__=='__main__':unittest.main(verbosity=2)
